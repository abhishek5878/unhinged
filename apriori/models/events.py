from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class EventTaxonomy(str, Enum):
    FINANCIAL_COLLAPSE = "financial_collapse"
    FAMILY_EMERGENCY = "family_emergency"
    CAREER_DISRUPTION = "career_disruption"
    HEALTH_CRISIS = "health_crisis"
    BETRAYAL = "betrayal"
    EXTERNAL_THREAT = "external_threat"
    VALUES_CONFLICT = "values_conflict"
    LOSS = "loss"


class BlackSwanEvent(BaseModel):
    """A high-impact stochastic crisis injected into a relational simulation."""

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: EventTaxonomy
    target_vulnerability_axis: str = Field(
        ..., description="Shadow vector dimension this event targets"
    )
    severity: float = Field(
        ..., ge=0.0, le=1.0, description="Pareto-distributed severity"
    )
    narrative_description: str = Field(
        ..., description="LLM-generated 3-sentence crisis scenario"
    )
    decision_point: str = Field(
        ..., description="Immediate choice agents must navigate"
    )
    expected_collapse_vector: Dict[str, float] = Field(
        ..., description="Predicted shadow delta per agent"
    )
    elasticity_threshold: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Below this score → Belief Collapse territory",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("narrative_description")
    @classmethod
    def validate_narrative(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("narrative_description must not be empty")
        return v

    @field_validator("decision_point")
    @classmethod
    def validate_decision_point(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("decision_point must not be empty")
        return v

    def __repr__(self) -> str:
        return (
            f"BlackSwanEvent(type={self.event_type.value}, "
            f"axis={self.target_vulnerability_axis!r}, "
            f"severity={self.severity:.2f})"
        )


class CrisisEpisode(BaseModel):
    """Full record of a crisis injection and its outcome."""

    episode_id: str = Field(default_factory=lambda: str(uuid4()))
    event: BlackSwanEvent
    pre_crisis_transcript: List[Dict] = Field(default_factory=list)
    post_crisis_transcript: List[Dict] = Field(default_factory=list)
    narrative_elasticity_score: float = Field(
        ..., ge=0.0, le=1.0, description="How well the pair absorbed the crisis"
    )
    reached_homeostasis: bool
    turns_to_resolution: Optional[int] = Field(
        default=None, ge=0, description="None if unresolved"
    )
    collapse_detected_at_turn: Optional[int] = Field(
        default=None, ge=0, description="Turn where BeliefCollapse was detected"
    )
    final_divergence: float = Field(
        ..., ge=0.0, description="Final epistemic divergence after episode"
    )

    @field_validator("final_divergence")
    @classmethod
    def validate_final_divergence(cls, v: float) -> float:
        if v < 0.0:
            raise ValueError("final_divergence must be >= 0.0")
        return v

    def __repr__(self) -> str:
        status = "homeostasis" if self.reached_homeostasis else "collapsed"
        return (
            f"CrisisEpisode(event={self.event.event_type.value}, "
            f"status={status}, "
            f"elasticity={self.narrative_elasticity_score:.2f}, "
            f"divergence={self.final_divergence:.3f})"
        )
