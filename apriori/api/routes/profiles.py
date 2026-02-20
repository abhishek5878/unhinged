"""Profile API routes — CRUD + pgvector compatibility candidate search."""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from apriori.api.deps import ClerkUser, get_current_user
from apriori.api.schemas import (
    CompatibilityCandidate,
    CompatibilityCandidatesResponse,
    ProfileCreateRequest,
    ProfileResponse,
    ProfileUpdateRequest,
)
from apriori.db.models import UserProfile
from apriori.db.session import get_session
from apriori.models.shadow_vector import AttachmentStyle, ShadowVector

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _compute_embedding(shadow: ShadowVector) -> list[float]:
    """Compute a 512-dim embedding from a ShadowVector using sentence-transformers.

    Constructs a natural-language description of the shadow vector and
    encodes it via a sentence transformer model. Pads/truncates to 512 dims.
    """
    from sentence_transformers import SentenceTransformer

    description = (
        f"A person with attachment style {shadow.attachment_style.value}. "
        f"Communication style: {shadow.communication_style}. "
        f"Core values: {', '.join(f'{k}={v:.2f}' for k, v in shadow.values.items())}. "
        f"Fears: {', '.join(shadow.fear_architecture) if shadow.fear_architecture else 'none'}. "
        f"Entropy tolerance: {shadow.entropy_tolerance:.2f}."
    )

    model = SentenceTransformer("all-MiniLM-L6-v2")
    raw = model.encode(description).tolist()

    # Pad to 512 or truncate
    if len(raw) < 512:
        raw.extend([0.0] * (512 - len(raw)))
    return raw[:512]


def _profile_to_response(profile: UserProfile) -> ProfileResponse:
    return ProfileResponse(
        user_id=profile.id,
        shadow_vector=profile.shadow_vector,
        embedding=list(profile.embedding) if profile.embedding else None,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


# ---------------------------------------------------------------------------
# POST /profiles
# ---------------------------------------------------------------------------


@router.post("", response_model=ProfileResponse)
async def create_profile(
    request: ProfileCreateRequest,
    session: AsyncSession = Depends(get_session),
) -> ProfileResponse:
    """Create a new user shadow vector profile.

    Validates fields, computes a 512-dim embedding via sentence-transformers,
    and persists the profile.
    """
    # Validate by constructing a ShadowVector (triggers Pydantic validators)
    shadow = ShadowVector(
        agent_id="temp",
        values=request.values,
        attachment_style=AttachmentStyle(request.attachment_style),
        fear_architecture=request.fear_architecture,
        linguistic_signature=request.linguistic_signature,
        entropy_tolerance=request.entropy_tolerance,
        communication_style=request.communication_style,
    )

    embedding = _compute_embedding(shadow)

    profile = UserProfile(
        shadow_vector={
            "values": request.values,
            "attachment_style": request.attachment_style,
            "fear_architecture": request.fear_architecture,
            "linguistic_signature": request.linguistic_signature,
            "entropy_tolerance": request.entropy_tolerance,
            "communication_style": request.communication_style,
        },
        embedding=embedding,
    )

    session.add(profile)
    await session.commit()
    await session.refresh(profile)

    return _profile_to_response(profile)


# ---------------------------------------------------------------------------
# GET /profiles/{user_id}
# ---------------------------------------------------------------------------


@router.get("/{user_id}", response_model=ProfileResponse)
async def get_profile(
    user_id: UUID,
    _user: ClerkUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ProfileResponse:
    """Retrieve a user's shadow vector profile."""
    profile = await session.get(UserProfile, user_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Profile {user_id} not found")
    return _profile_to_response(profile)


# ---------------------------------------------------------------------------
# PUT /profiles/{user_id}
# ---------------------------------------------------------------------------


@router.put("/{user_id}", response_model=ProfileResponse)
async def update_profile(
    user_id: UUID,
    request: ProfileUpdateRequest,
    _user: ClerkUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ProfileResponse:
    """Partial update of shadow vector fields.

    Only provided (non-None) fields are updated. Recomputes the embedding
    after any change.
    """
    profile = await session.get(UserProfile, user_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Profile {user_id} not found")

    sv = dict(profile.shadow_vector)
    update_data = request.model_dump(exclude_none=True)

    for key, value in update_data.items():
        sv[key] = value

    # Validate updated vector
    shadow = ShadowVector(
        agent_id=str(user_id),
        values=sv["values"],
        attachment_style=AttachmentStyle(sv["attachment_style"]),
        fear_architecture=sv.get("fear_architecture", []),
        linguistic_signature=sv.get("linguistic_signature", []),
        entropy_tolerance=sv.get("entropy_tolerance", 0.5),
        communication_style=sv.get("communication_style", "direct"),
    )

    profile.shadow_vector = sv
    profile.embedding = _compute_embedding(shadow)

    await session.commit()
    await session.refresh(profile)

    return _profile_to_response(profile)


# ---------------------------------------------------------------------------
# GET /profiles/{user_id}/compatibility-candidates
# ---------------------------------------------------------------------------


@router.get(
    "/{user_id}/compatibility-candidates",
    response_model=CompatibilityCandidatesResponse,
)
async def get_compatibility_candidates(
    user_id: UUID,
    limit: int = Query(default=10, ge=1, le=100),
    min_score: float = Query(default=0.6, ge=0.0, le=1.0),
    _user: ClerkUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> CompatibilityCandidatesResponse:
    """Find top compatibility candidates via pgvector cosine similarity.

    This is a FIRST-ORDER approximation using embedding distance.
    Full Monte Carlo simulation is required for ground truth.

    Uses the IVFFlat index on user_profiles.embedding with
    cosine distance operator (<=>).
    """
    profile = await session.get(UserProfile, user_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Profile {user_id} not found")
    if profile.embedding is None:
        raise HTTPException(status_code=409, detail="Profile has no embedding")

    # pgvector cosine distance: <=> returns distance (0=identical, 2=opposite)
    # similarity = 1 - distance
    embedding_str = "[" + ",".join(str(x) for x in profile.embedding) + "]"

    query = text("""
        SELECT
            id,
            shadow_vector,
            1 - (embedding <=> :embedding::vector) AS similarity
        FROM user_profiles
        WHERE id != :user_id
          AND embedding IS NOT NULL
          AND 1 - (embedding <=> :embedding::vector) >= :min_score
        ORDER BY embedding <=> :embedding::vector
        LIMIT :limit
    """)

    result = await session.execute(
        query,
        {
            "embedding": embedding_str,
            "user_id": str(user_id),
            "min_score": min_score,
            "limit": limit,
        },
    )

    candidates = []
    for row in result.fetchall():
        sv = row[1] if isinstance(row[1], dict) else {}
        candidates.append(
            CompatibilityCandidate(
                user_id=row[0],
                similarity_score=round(float(row[2]), 4),
                attachment_style=sv.get("attachment_style", "unknown"),
                communication_style=sv.get("communication_style", "unknown"),
            )
        )

    return CompatibilityCandidatesResponse(
        query_user_id=user_id,
        candidates=candidates,
        total=len(candidates),
    )
