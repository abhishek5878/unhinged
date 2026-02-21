"""Simulation invite routes — create, look up, and claim invite tokens."""

from __future__ import annotations

import logging
import secrets
import string
from datetime import datetime, timezone, timedelta
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apriori.api.deps import ClerkUser, get_current_user
from apriori.db.models import SimulationInvite, SimulationRun, UserProfile
from apriori.db.session import get_session

logger = logging.getLogger(__name__)

router = APIRouter()

_TOKEN_TTL_HOURS = 72


def _make_token(length: int = 12) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


# ── Schemas ──────────────────────────────────────────────────────────────────


class CreateInviteResponse(BaseModel):
    token: str
    link_path: str
    expires_at: datetime


class InviteInfoResponse(BaseModel):
    token: str
    status: str  # "pending" | "claimed" | "expired"
    inviter_attachment_style: str
    inviter_has_shadow_vector: bool
    expires_at: datetime


class ClaimInviteResponse(BaseModel):
    simulation_id: str
    status: str
    eta_seconds: int


# ── Routes ────────────────────────────────────────────────────────────────────


@router.post("", response_model=CreateInviteResponse)
async def create_invite(
    user: ClerkUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> CreateInviteResponse:
    """Create a new simulation invite token (auth required)."""
    # Resolve inviter profile
    result = await session.execute(
        select(UserProfile).where(UserProfile.clerk_user_id == user.user_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    token = _make_token()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=_TOKEN_TTL_HOURS)

    invite = SimulationInvite(
        token=token,
        inviter_user_id=profile.id,
        expires_at=expires_at,
        status="pending",
    )
    session.add(invite)
    await session.commit()

    logger.info("Invite created: token=%s inviter=%s", token, profile.id)

    return CreateInviteResponse(
        token=token,
        link_path=f"/simulate/invite/{token}",
        expires_at=expires_at,
    )


@router.get("/{token}", response_model=InviteInfoResponse)
async def get_invite(
    token: str,
    session: AsyncSession = Depends(get_session),
) -> InviteInfoResponse:
    """Look up an invite token (public — no auth required)."""
    result = await session.execute(
        select(SimulationInvite).where(SimulationInvite.token == token)
    )
    invite = result.scalar_one_or_none()
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")

    now = datetime.now(timezone.utc)
    if invite.status == "pending" and invite.expires_at < now:
        invite.status = "expired"
        await session.commit()

    inviter = await session.get(UserProfile, invite.inviter_user_id)
    sv = inviter.shadow_vector if inviter else {}
    has_sv = bool(sv and sv.get("values"))
    attachment = sv.get("attachment_style", "unknown") if isinstance(sv, dict) else "unknown"

    return InviteInfoResponse(
        token=invite.token,
        status=invite.status,
        inviter_attachment_style=attachment,
        inviter_has_shadow_vector=has_sv,
        expires_at=invite.expires_at,
    )


@router.post("/{token}/claim", response_model=ClaimInviteResponse)
async def claim_invite(
    token: str,
    request: Request,
    background_tasks: BackgroundTasks,
    user: ClerkUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ClaimInviteResponse:
    """Claim an invite: pair invitee with inviter and launch a simulation."""
    result = await session.execute(
        select(SimulationInvite).where(SimulationInvite.token == token)
    )
    invite = result.scalar_one_or_none()
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")

    now = datetime.now(timezone.utc)
    if invite.status != "pending":
        raise HTTPException(status_code=409, detail=f"Invite already {invite.status}")
    if invite.expires_at < now:
        invite.status = "expired"
        await session.commit()
        raise HTTPException(status_code=410, detail="Invite has expired")

    # Resolve invitee profile
    invitee_result = await session.execute(
        select(UserProfile).where(UserProfile.clerk_user_id == user.user_id)
    )
    invitee = invitee_result.scalar_one_or_none()
    if not invitee:
        raise HTTPException(status_code=404, detail="Your profile not found — complete onboarding first")
    if not (invitee.shadow_vector and invitee.shadow_vector.get("values")):
        raise HTTPException(status_code=409, detail="Complete your Shadow Vector first")
    if str(invitee.id) == str(invite.inviter_user_id):
        raise HTTPException(status_code=400, detail="Cannot simulate with yourself")

    # Mark invite claimed
    invite.invitee_user_id = invitee.id
    invite.status = "claimed"

    # Create simulation record inline
    from uuid import uuid4
    from apriori.db.models import SimulationRun

    pair_id = f"{invite.inviter_user_id}_{invitee.id}"
    sim_id = uuid4()
    n_timelines = 20  # fast mode for invite flow
    sim_run = SimulationRun(
        id=sim_id,
        pair_id=pair_id,
        user_a_id=invite.inviter_user_id,
        user_b_id=invitee.id,
        status="running",
        n_timelines=n_timelines,
    )
    session.add(sim_run)
    invite.simulation_run_id = sim_id
    await session.commit()

    # Run simulation as background task
    inviter = await session.get(UserProfile, invite.inviter_user_id)

    from apriori.api.routes.simulate import _shadow_from_profile, _run_inline_simulation
    from apriori.db.session import async_session as session_factory
    from apriori.config import settings

    shadow_a = _shadow_from_profile(inviter)
    shadow_b = _shadow_from_profile(invitee)
    background_tasks.add_task(
        _run_inline_simulation,
        sim_id,
        shadow_a,
        shadow_b,
        pair_id,
        n_timelines,
        (0.3, 0.9),
        session_factory,
    )

    logger.info("Invite claimed: token=%s sim_id=%s", token, sim_id)

    return ClaimInviteResponse(
        simulation_id=str(sim_id),
        status="running",
        eta_seconds=n_timelines * 15,
    )
