"""SQLAlchemy ORM models for the APRIORI persistence layer."""

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apriori.db.session import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UserProfile(Base):
    """User shadow vector profile with pgvector embedding."""

    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    clerk_user_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, unique=True, index=True
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True
    )
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    shadow_vector: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    onboarding_complete: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    embedding: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    # Relationships (string refs for forward declarations)
    simulations_as_a: Mapped[List["SimulationRun"]] = relationship(
        back_populates="user_a", foreign_keys="SimulationRun.user_a_id"
    )
    simulations_as_b: Mapped[List["SimulationRun"]] = relationship(
        back_populates="user_b", foreign_keys="SimulationRun.user_b_id"
    )
    linguistic_profiles: Mapped[List["LinguisticProfileRecord"]] = relationship(
        back_populates="user"
    )

    __table_args__ = ()

    def __repr__(self) -> str:
        return f"UserProfile(id={self.id!s:.8}…)"


class SimulationRun(Base):
    """Record of a Monte Carlo simulation run."""

    __tablename__ = "simulation_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    pair_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    user_a_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user_profiles.id"), nullable=False
    )
    user_b_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user_profiles.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )
    temporal_workflow_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    n_timelines: Mapped[int] = mapped_column(Integer, nullable=False)
    results: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    user_a: Mapped[UserProfile] = relationship(
        back_populates="simulations_as_a", foreign_keys=[user_a_id]
    )
    user_b: Mapped[UserProfile] = relationship(
        back_populates="simulations_as_b", foreign_keys=[user_b_id]
    )
    crisis_episodes: Mapped[List["CrisisEpisodeRecord"]] = relationship(
        back_populates="simulation_run"
    )

    def __repr__(self) -> str:
        return (
            f"SimulationRun(id={self.id!s:.8}…, "
            f"pair={self.pair_id!r}, status={self.status!r})"
        )


class CrisisEpisodeRecord(Base):
    """Persisted crisis episode from a simulation timeline."""

    __tablename__ = "crisis_episodes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    simulation_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("simulation_runs.id"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[float] = mapped_column(Float, nullable=False)
    vulnerability_axis: Mapped[str] = mapped_column(String(50), nullable=False)
    narrative_elasticity: Mapped[float] = mapped_column(Float, nullable=False)
    reached_homeostasis: Mapped[bool] = mapped_column(Boolean, nullable=False)
    transcript: Mapped[dict] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )

    # Relationships
    simulation_run: Mapped[SimulationRun] = relationship(
        back_populates="crisis_episodes"
    )

    def __repr__(self) -> str:
        status = "H" if self.reached_homeostasis else "C"
        return (
            f"CrisisEpisodeRecord(id={self.id!s:.8}…, "
            f"type={self.event_type!r}, sev={self.severity:.2f}, [{status}])"
        )


class LinguisticProfileRecord(Base):
    """Persisted linguistic profile tracking convergence history."""

    __tablename__ = "linguistic_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user_profiles.id"), nullable=False
    )
    phrase_registry: Mapped[dict] = mapped_column(JSONB, default=dict)
    convergence_history: Mapped[dict] = mapped_column(JSONB, default=dict)
    last_simulation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("simulation_runs.id"),
        nullable=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    # Relationships
    user: Mapped[UserProfile] = relationship(back_populates="linguistic_profiles")

    def __repr__(self) -> str:
        return f"LinguisticProfileRecord(id={self.id!s:.8}…, user={self.user_id!s:.8}…)"


class SimulationInvite(Base):
    """Invite token allowing a user to pair with another for a simulation."""

    __tablename__ = "simulation_invites"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    token: Mapped[str] = mapped_column(
        String(16), nullable=False, unique=True, index=True
    )
    inviter_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user_profiles.id"), nullable=False
    )
    invitee_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user_profiles.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    simulation_run_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("simulation_runs.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )

    def __repr__(self) -> str:
        return f"SimulationInvite(token={self.token!r}, status={self.status!r})"


class WaitlistSignup(Base):
    """Waitlist signup for early access."""

    __tablename__ = "waitlist_signups"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    partner_email: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    referral_code: Mapped[str] = mapped_column(
        String(20), nullable=False, unique=True, index=True
    )
    referral_code_used: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="waiting"
    )
    clerk_user_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )

    def __repr__(self) -> str:
        return (
            f"WaitlistSignup(id={self.id!s:.8}…, "
            f"email={self.email!r}, pos={self.position})"
        )


class WaitlistEntry(Base):
    """Revamped waitlist entry with city-based clustering and referral tracking."""

    __tablename__ = "waitlist_entries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    city: Mapped[str] = mapped_column(String(255), nullable=False)
    referral_code: Mapped[str] = mapped_column(
        String(20), nullable=False, unique=True, index=True
    )
    referred_by: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, index=True
    )
    referral_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )
    converted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    converted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    source: Mapped[str] = mapped_column(
        String(50), nullable=False, default="organic"
    )

    def __repr__(self) -> str:
        return (
            f"WaitlistEntry(id={self.id!s:.8}…, "
            f"email={self.email!r}, city={self.city!r}, pos={self.position})"
        )
