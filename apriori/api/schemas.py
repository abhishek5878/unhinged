"""Pydantic request/response schemas for the APRIORI API."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# ---------------------------------------------------------------------------
# Profile schemas
# ---------------------------------------------------------------------------


class ProfileCreateRequest(BaseModel):
    """Create a new user shadow vector profile."""

    values: Dict[str, float] = Field(
        ...,
        description="Shadow vector value dimensions (each 0.0-1.0)",
        json_schema_extra={
            "example": {
                "autonomy": 0.7, "security": 0.4, "achievement": 0.8,
                "intimacy": 0.5, "novelty": 0.6, "stability": 0.3,
                "power": 0.5, "belonging": 0.6,
            }
        },
    )
    attachment_style: str = Field(
        ...,
        description="Attachment style: secure, anxious, avoidant, or fearful",
        json_schema_extra={"example": "secure"},
    )
    fear_architecture: List[str] = Field(
        ...,
        description="Core fears driving relational behavior",
        json_schema_extra={"example": ["abandonment", "engulfment"]},
    )
    linguistic_signature: List[str] = Field(
        default_factory=list,
        description="Takiya-kalaam / signature phrases",
        json_schema_extra={"example": ["you know what I mean", "at the end of the day"]},
    )
    entropy_tolerance: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Stress flexibility (0.0=rigid, 1.0=fluid)",
        json_schema_extra={"example": 0.6},
    )
    communication_style: str = Field(
        ...,
        description="Communication style: direct, indirect, aggressive, or passive",
        json_schema_extra={"example": "direct"},
    )

    model_config = {"json_schema_extra": {"example": {
        "values": {
            "autonomy": 0.7, "security": 0.4, "achievement": 0.8,
            "intimacy": 0.5, "novelty": 0.6, "stability": 0.3,
            "power": 0.5, "belonging": 0.6,
        },
        "attachment_style": "secure",
        "fear_architecture": ["abandonment", "engulfment"],
        "linguistic_signature": ["you know what I mean"],
        "entropy_tolerance": 0.6,
        "communication_style": "direct",
    }}}


class ProfileResponse(BaseModel):
    """Response with full user profile data."""

    user_id: UUID = Field(..., json_schema_extra={"example": "550e8400-e29b-41d4-a716-446655440000"})
    shadow_vector: dict = Field(..., description="Full ShadowVector as JSON")
    embedding: Optional[List[float]] = Field(
        None, description="512-dim latent embedding"
    )
    created_at: datetime
    updated_at: datetime


class ProfileUpdateRequest(BaseModel):
    """Partial update of shadow vector fields."""

    values: Optional[Dict[str, float]] = None
    attachment_style: Optional[str] = None
    fear_architecture: Optional[List[str]] = None
    linguistic_signature: Optional[List[str]] = None
    entropy_tolerance: Optional[float] = Field(None, ge=0.0, le=1.0)
    communication_style: Optional[str] = None


class CompatibilityCandidate(BaseModel):
    """A candidate user ranked by embedding similarity."""

    user_id: UUID
    similarity_score: float = Field(
        ..., ge=0.0, le=1.0, description="Cosine similarity (1.0 = identical)"
    )
    attachment_style: str
    communication_style: str


class CompatibilityCandidatesResponse(BaseModel):
    """List of compatibility candidates from pgvector search."""

    query_user_id: UUID
    candidates: List[CompatibilityCandidate]
    total: int


# ---------------------------------------------------------------------------
# Simulation schemas
# ---------------------------------------------------------------------------


class SimulationCreateRequest(BaseModel):
    """Launch a new Monte Carlo relational simulation."""

    user_a_id: UUID = Field(
        ...,
        description="First user profile ID",
        json_schema_extra={"example": "550e8400-e29b-41d4-a716-446655440000"},
    )
    user_b_id: UUID = Field(
        ...,
        description="Second user profile ID",
        json_schema_extra={"example": "660e8400-e29b-41d4-a716-446655440001"},
    )
    n_timelines: int = Field(
        default=20,
        ge=1,
        le=500,
        description="Number of Monte Carlo timelines to simulate",
        json_schema_extra={"example": 20},
    )
    fast_mode: bool = Field(
        default=True,
        description="Fast mode: 20 timelines, 15 turns (~3-5 min). Set False for full 100-timeline run (~20 min).",
    )
    use_temporal: Optional[bool] = Field(
        default=None,
        description="Use Temporal workflow (defaults to True for n>20)",
    )
    crisis_severity_range: Optional[Tuple[float, float]] = Field(
        default=None,
        description="(min, max) crisis severity override",
        json_schema_extra={"example": [0.1, 0.9]},
    )

    model_config = {"json_schema_extra": {"example": {
        "user_a_id": "550e8400-e29b-41d4-a716-446655440000",
        "user_b_id": "660e8400-e29b-41d4-a716-446655440001",
        "n_timelines": 100,
    }}}


class SimulationCreateResponse(BaseModel):
    """Response after queuing a simulation."""

    simulation_id: UUID
    status: str = Field(
        ...,
        description="'queued' or 'running'",
        json_schema_extra={"example": "queued"},
    )
    eta_seconds: int = Field(
        ...,
        description="Estimated time to completion in seconds",
        json_schema_extra={"example": 300},
    )


class SimulationStatusResponse(BaseModel):
    """Full simulation run status with results if completed."""

    simulation_id: UUID
    pair_id: str
    status: str
    n_timelines: int
    temporal_workflow_id: Optional[str] = None
    results: Optional[dict] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class SimulationReportResponse(BaseModel):
    """Executive report as plain text."""

    simulation_id: UUID
    report: str


class SimulationProgressMessage(BaseModel):
    """WebSocket progress update message."""

    completed: int
    total: int
    status: str
    percent: float = Field(..., ge=0.0, le=100.0)


# ---------------------------------------------------------------------------
# Auth schemas
# ---------------------------------------------------------------------------


class SyncUserRequest(BaseModel):
    """Webhook payload to sync a Clerk user into our database."""

    clerk_user_id: str
    email: str
    name: str = ""


class SyncUserResponse(BaseModel):
    """Response after syncing a user."""

    user_id: UUID
    created: bool


class MeResponse(BaseModel):
    """Current authenticated user's profile summary."""

    user_id: UUID
    clerk_user_id: str
    email: Optional[str] = None
    name: Optional[str] = None
    has_shadow_vector: bool
    onboarding_complete: bool
    simulation_count: int


# ---------------------------------------------------------------------------
# Waitlist schemas
# ---------------------------------------------------------------------------


class WaitlistSignupRequest(BaseModel):
    """Join the APRIORI MATCH waitlist."""

    name: str = Field(
        ..., min_length=1, max_length=255, json_schema_extra={"example": "Arjun Sharma"}
    )
    email: EmailStr = Field(
        ..., json_schema_extra={"example": "arjun@example.com"}
    )
    partner_email: Optional[EmailStr] = Field(
        default=None, json_schema_extra={"example": "priya@example.com"}
    )
    referral_code_used: Optional[str] = Field(
        default=None, max_length=20, json_schema_extra={"example": "ABC12345"}
    )


class WaitlistSignupResponse(BaseModel):
    """Response after joining the waitlist."""

    id: UUID
    email: str
    name: str
    partner_email: Optional[str] = None
    position: int
    referral_code: str
    status: str
    created_at: datetime


class WaitlistPositionResponse(BaseModel):
    """Current waitlist position for an authenticated user."""

    email: str
    position: int
    referral_code: str
    status: str
    total_signups: int


# ---------------------------------------------------------------------------
# WaitlistEntry schemas (revamped waitlist with city + referral tracking)
# ---------------------------------------------------------------------------


class WaitlistEntryRequest(BaseModel):
    """Join the APRIORI MATCH waitlist (revamped)."""

    email: EmailStr = Field(
        ..., json_schema_extra={"example": "arjun@example.com"}
    )
    city: str = Field(
        ..., min_length=1, max_length=255, json_schema_extra={"example": "Mumbai"}
    )
    ref: Optional[str] = Field(
        default=None, max_length=20, json_schema_extra={"example": "ABC12345"}
    )
    source: str = Field(
        default="organic", max_length=50, json_schema_extra={"example": "organic"}
    )


class WaitlistEntryResponse(BaseModel):
    """Response after joining the waitlist."""

    email: str
    city: str
    position: int
    referral_code: str
    referral_count: int
    total_signups: int


class WaitlistCheckResponse(BaseModel):
    """Check if an email is already on the waitlist."""

    on_waitlist: bool
    position: Optional[int] = None
    referral_code: Optional[str] = None
    referral_count: int = 0


class WaitlistStatsResponse(BaseModel):
    """Admin stats for the waitlist."""

    total: int
    cities: Dict[str, int]
    sources: Dict[str, int]
    conversions: int
