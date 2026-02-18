"""Waitlist API routes — signup, position lookup, authenticated status."""

from __future__ import annotations

import logging
import secrets
import string

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from apriori.api.deps import ClerkUser, get_current_user
from apriori.api.schemas import (
    WaitlistCheckResponse,
    WaitlistEntryRequest,
    WaitlistEntryResponse,
    WaitlistPositionResponse,
    WaitlistSignupRequest,
    WaitlistSignupResponse,
    WaitlistStatsResponse,
)
from apriori.db.models import WaitlistEntry, WaitlistSignup
from apriori.db.session import get_session

logger = logging.getLogger(__name__)

router = APIRouter()


def _generate_referral_code(length: int = 8) -> str:
    """Generate a random alphanumeric referral code."""
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


# ---------------------------------------------------------------------------
# POST /waitlist  (revamped — email + city + referral)
# ---------------------------------------------------------------------------


@router.post("", response_model=WaitlistEntryResponse)
async def join_waitlist(
    request: WaitlistEntryRequest,
    session: AsyncSession = Depends(get_session),
) -> WaitlistEntryResponse:
    """Join the APRIORI MATCH waitlist (public, no auth required)."""
    # Check for duplicate email
    existing = await session.execute(
        select(WaitlistEntry).where(WaitlistEntry.email == request.email)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail="This email is already on the waitlist",
        )

    # Compute position
    count_result = await session.execute(
        select(func.count()).select_from(WaitlistEntry)
    )
    position = count_result.scalar_one() + 1

    # Generate unique referral code
    referral_code = _generate_referral_code()

    entry = WaitlistEntry(
        email=request.email,
        city=request.city,
        referral_code=referral_code,
        referred_by=request.ref,
        position=position,
        source=request.source or "organic",
    )

    session.add(entry)

    # Bump referral count for the referrer
    if request.ref:
        referrer_result = await session.execute(
            select(WaitlistEntry).where(
                WaitlistEntry.referral_code == request.ref
            )
        )
        referrer = referrer_result.scalar_one_or_none()
        if referrer:
            referrer.referral_count += 1

    await session.commit()
    await session.refresh(entry)

    total_result = await session.execute(
        select(func.count()).select_from(WaitlistEntry)
    )
    total = total_result.scalar_one()

    logger.info(
        "Waitlist entry #%d: %s from %s (referral: %s, ref_by: %s)",
        position,
        request.email,
        request.city,
        referral_code,
        request.ref,
    )

    return WaitlistEntryResponse(
        email=entry.email,
        city=entry.city,
        position=entry.position,
        referral_code=entry.referral_code,
        referral_count=entry.referral_count,
        total_signups=total,
    )


# ---------------------------------------------------------------------------
# GET /waitlist/check?email=...  (public)
# ---------------------------------------------------------------------------


@router.get("/check", response_model=WaitlistCheckResponse)
async def check_waitlist(
    email: str,
    session: AsyncSession = Depends(get_session),
) -> WaitlistCheckResponse:
    """Check if an email is already on the waitlist."""
    result = await session.execute(
        select(WaitlistEntry).where(WaitlistEntry.email == email)
    )
    entry = result.scalar_one_or_none()

    if entry is None:
        return WaitlistCheckResponse(on_waitlist=False)

    return WaitlistCheckResponse(
        on_waitlist=True,
        position=entry.position,
        referral_code=entry.referral_code,
        referral_count=entry.referral_count,
    )


# ---------------------------------------------------------------------------
# GET /waitlist/stats  (admin)
# ---------------------------------------------------------------------------


@router.get("/stats", response_model=WaitlistStatsResponse)
async def get_waitlist_stats(
    session: AsyncSession = Depends(get_session),
) -> WaitlistStatsResponse:
    """Get waitlist stats (city breakdown, sources, conversions)."""
    total_result = await session.execute(
        select(func.count()).select_from(WaitlistEntry)
    )
    total = total_result.scalar_one()

    # City breakdown
    city_rows = await session.execute(
        select(WaitlistEntry.city, func.count())
        .group_by(WaitlistEntry.city)
        .order_by(func.count().desc())
    )
    cities = {row[0]: row[1] for row in city_rows.all()}

    # Source breakdown
    source_rows = await session.execute(
        select(WaitlistEntry.source, func.count())
        .group_by(WaitlistEntry.source)
        .order_by(func.count().desc())
    )
    sources = {row[0]: row[1] for row in source_rows.all()}

    # Conversions
    conv_result = await session.execute(
        select(func.count())
        .select_from(WaitlistEntry)
        .where(WaitlistEntry.converted.is_(True))
    )
    conversions = conv_result.scalar_one()

    return WaitlistStatsResponse(
        total=total,
        cities=cities,
        sources=sources,
        conversions=conversions,
    )


# ---------------------------------------------------------------------------
# Legacy endpoints (from old WaitlistSignup model)
# ---------------------------------------------------------------------------


@router.post("/legacy", response_model=WaitlistSignupResponse)
async def join_waitlist_legacy(
    request: WaitlistSignupRequest,
    session: AsyncSession = Depends(get_session),
) -> WaitlistSignupResponse:
    """Legacy waitlist signup endpoint."""
    existing = await session.execute(
        select(WaitlistSignup).where(WaitlistSignup.email == request.email)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail="This email is already on the waitlist",
        )

    count_result = await session.execute(
        select(func.count()).select_from(WaitlistSignup)
    )
    position = count_result.scalar_one() + 1

    referral_code = _generate_referral_code()

    signup = WaitlistSignup(
        email=request.email,
        name=request.name,
        partner_email=request.partner_email,
        referral_code=referral_code,
        referral_code_used=request.referral_code_used,
        position=position,
        status="waiting",
    )

    session.add(signup)
    await session.commit()
    await session.refresh(signup)

    return WaitlistSignupResponse(
        id=signup.id,
        email=signup.email,
        name=signup.name,
        partner_email=signup.partner_email,
        position=signup.position,
        referral_code=signup.referral_code,
        status=signup.status,
        created_at=signup.created_at,
    )


@router.get("/me", response_model=WaitlistPositionResponse)
async def get_my_position(
    user: ClerkUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> WaitlistPositionResponse:
    """Get the authenticated user's waitlist position."""
    signup = None

    if user.user_id:
        result = await session.execute(
            select(WaitlistSignup).where(
                WaitlistSignup.clerk_user_id == user.user_id
            )
        )
        signup = result.scalar_one_or_none()

    if signup is None and user.email:
        result = await session.execute(
            select(WaitlistSignup).where(
                WaitlistSignup.email == user.email
            )
        )
        signup = result.scalar_one_or_none()

        if signup and not signup.clerk_user_id:
            signup.clerk_user_id = user.user_id
            await session.commit()
            await session.refresh(signup)

    if signup is None:
        raise HTTPException(
            status_code=404,
            detail="No waitlist entry found for this account",
        )

    total_result = await session.execute(
        select(func.count()).select_from(WaitlistSignup)
    )
    total = total_result.scalar_one()

    return WaitlistPositionResponse(
        email=signup.email,
        position=signup.position,
        referral_code=signup.referral_code,
        status=signup.status,
        total_signups=total,
    )
