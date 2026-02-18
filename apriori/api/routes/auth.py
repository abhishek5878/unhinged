"""Auth API routes — Clerk user sync and authenticated user info."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from apriori.api.deps import ClerkUser, get_current_user
from apriori.api.schemas import MeResponse, SyncUserRequest, SyncUserResponse
from apriori.db.models import SimulationRun, UserProfile
from apriori.db.session import get_session

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# POST /auth/sync-user  (called by Clerk webhook)
# ---------------------------------------------------------------------------


@router.post("/sync-user", response_model=SyncUserResponse)
async def sync_user(
    request: SyncUserRequest,
    session: AsyncSession = Depends(get_session),
) -> SyncUserResponse:
    """Create or return a UserProfile for a Clerk user. Idempotent."""
    result = await session.execute(
        select(UserProfile).where(
            UserProfile.clerk_user_id == request.clerk_user_id
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        return SyncUserResponse(user_id=existing.id, created=False)

    profile = UserProfile(
        clerk_user_id=request.clerk_user_id,
        email=request.email,
        name=request.name,
        shadow_vector={},
        onboarding_complete=False,
    )

    session.add(profile)
    await session.commit()
    await session.refresh(profile)

    logger.info("Synced new user: clerk_id=%s, user_id=%s", request.clerk_user_id, profile.id)

    return SyncUserResponse(user_id=profile.id, created=True)


# ---------------------------------------------------------------------------
# POST /users/{clerk_user_id}/soft-delete  (called by Clerk webhook)
# ---------------------------------------------------------------------------


@router.post("/users/{clerk_user_id}/soft-delete")
async def soft_delete_user(
    clerk_user_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Soft-delete a user when their Clerk account is deleted."""
    result = await session.execute(
        select(UserProfile).where(
            UserProfile.clerk_user_id == clerk_user_id
        )
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(status_code=404, detail="User not found")

    profile.is_deleted = True
    await session.commit()

    logger.info("Soft-deleted user: clerk_id=%s", clerk_user_id)
    return {"status": "deleted", "clerk_user_id": clerk_user_id}


# ---------------------------------------------------------------------------
# GET /auth/me  (authenticated)
# ---------------------------------------------------------------------------


@router.get("/me", response_model=MeResponse)
async def get_me(
    user: ClerkUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> MeResponse:
    """Return the authenticated user's profile summary."""
    result = await session.execute(
        select(UserProfile).where(
            UserProfile.clerk_user_id == user.user_id
        )
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")

    sim_count_result = await session.execute(
        select(func.count()).select_from(SimulationRun).where(
            (SimulationRun.user_a_id == profile.id)
            | (SimulationRun.user_b_id == profile.id)
        )
    )
    simulation_count = sim_count_result.scalar_one()

    has_shadow_vector = bool(
        profile.shadow_vector and profile.shadow_vector.get("values")
    )

    return MeResponse(
        user_id=profile.id,
        clerk_user_id=profile.clerk_user_id or "",
        email=profile.email,
        name=profile.name,
        has_shadow_vector=has_shadow_vector,
        onboarding_complete=profile.onboarding_complete,
        simulation_count=simulation_count,
    )
