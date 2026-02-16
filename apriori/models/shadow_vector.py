from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


SHADOW_VALUE_KEYS = frozenset(
    [
        "autonomy",
        "security",
        "achievement",
        "intimacy",
        "novelty",
        "stability",
        "power",
        "belonging",
    ]
)

COMMUNICATION_STYLES = {"direct", "indirect", "aggressive", "passive"}


class AttachmentStyle(str, Enum):
    SECURE = "secure"
    ANXIOUS = "anxious"
    AVOIDANT = "avoidant"
    FEARFUL = "fearful"


class ShadowVector(BaseModel):
    """Ground truth latent state of an agent. Never directly exposed in dialogue."""

    agent_id: str
    values: Dict[str, float] = Field(
        ...,
        description=(
            "Keys: autonomy, security, achievement, intimacy, novelty, "
            "stability, power, belonging — each 0.0-1.0"
        ),
    )
    attachment_style: AttachmentStyle
    fear_architecture: List[str] = Field(
        ...,
        description='e.g. ["abandonment", "failure", "engulfment"]',
    )
    linguistic_signature: List[str] = Field(
        ...,
        description="Takiya-kalaam / signature phrases",
    )
    entropy_tolerance: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="0.0 (rigid) → 1.0 (fluid) — stress response flexibility",
    )
    communication_style: str = Field(
        ...,
        description="direct | indirect | aggressive | passive",
    )
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("values")
    @classmethod
    def validate_values(cls, v: Dict[str, float]) -> Dict[str, float]:
        if set(v.keys()) != SHADOW_VALUE_KEYS:
            missing = SHADOW_VALUE_KEYS - set(v.keys())
            extra = set(v.keys()) - SHADOW_VALUE_KEYS
            parts: list[str] = []
            if missing:
                parts.append(f"missing: {sorted(missing)}")
            if extra:
                parts.append(f"extra: {sorted(extra)}")
            raise ValueError(
                f"values must contain exactly {sorted(SHADOW_VALUE_KEYS)}. {', '.join(parts)}"
            )
        for key, val in v.items():
            if not 0.0 <= val <= 1.0:
                raise ValueError(f"values['{key}'] = {val} must be between 0.0 and 1.0")
        total = sum(v.values())
        if total > 8.0:
            raise ValueError(f"values sum {total:.2f} exceeds maximum of 8.0")
        return v

    @field_validator("communication_style")
    @classmethod
    def validate_communication_style(cls, v: str) -> str:
        if v not in COMMUNICATION_STYLES:
            raise ValueError(f"communication_style must be one of {sorted(COMMUNICATION_STYLES)}, got '{v}'")
        return v

    def __repr__(self) -> str:
        top_values = sorted(self.values.items(), key=lambda x: x[1], reverse=True)[:3]
        top_str = ", ".join(f"{k}={v:.2f}" for k, v in top_values)
        return (
            f"ShadowVector(agent_id={self.agent_id!r}, "
            f"attachment={self.attachment_style.value}, "
            f"top=[{top_str}], "
            f"entropy={self.entropy_tolerance:.2f})"
        )


class EpistemicModel(BaseModel):
    """What agent A believes about agent B's inner world — and beyond."""

    owner_agent_id: str
    target_agent_id: str
    l1_belief: ShadowVector = Field(
        ..., description="A's model of B"
    )
    l2_belief: ShadowVector = Field(
        ..., description="A's model of (B's model of A)"
    )
    l3_belief: Optional[ShadowVector] = Field(
        default=None, description="4th-order recursive loop (depth-gated)"
    )
    belief_confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Bayesian posterior confidence"
    )
    epistemic_divergence: float = Field(
        ..., ge=0.0, description="KL(L1, L2) — pre-collapse signal"
    )
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    update_count: int = 0

    @model_validator(mode="after")
    def validate_agent_ids(self) -> EpistemicModel:
        if self.owner_agent_id == self.target_agent_id:
            raise ValueError("owner_agent_id and target_agent_id must differ")
        return self

    def __repr__(self) -> str:
        depth = "L3" if self.l3_belief is not None else "L2"
        return (
            f"EpistemicModel({self.owner_agent_id!r}→{self.target_agent_id!r}, "
            f"depth={depth}, confidence={self.belief_confidence:.2f}, "
            f"divergence={self.epistemic_divergence:.3f})"
        )


class BeliefState(BaseModel):
    """Full snapshot of an agent's cognitive state at a moment in time."""

    agent_id: str
    shadow: ShadowVector
    epistemic_models: Dict[str, EpistemicModel] = Field(
        default_factory=dict,
        description="Keyed by target agent_id",
    )
    hidden_thought_log: List[Dict[str, Any]] = Field(default_factory=list)
    turn_number: int = 0

    @model_validator(mode="after")
    def validate_consistency(self) -> BeliefState:
        if self.shadow.agent_id != self.agent_id:
            raise ValueError(
                f"shadow.agent_id ({self.shadow.agent_id!r}) must match "
                f"agent_id ({self.agent_id!r})"
            )
        for target_id, model in self.epistemic_models.items():
            if model.owner_agent_id != self.agent_id:
                raise ValueError(
                    f"epistemic_models['{target_id}'].owner_agent_id "
                    f"({model.owner_agent_id!r}) must match agent_id ({self.agent_id!r})"
                )
            if model.target_agent_id != target_id:
                raise ValueError(
                    f"epistemic_models key '{target_id}' does not match "
                    f"model.target_agent_id ({model.target_agent_id!r})"
                )
        return self

    def __repr__(self) -> str:
        return (
            f"BeliefState(agent={self.agent_id!r}, "
            f"turn={self.turn_number}, "
            f"models={list(self.epistemic_models.keys())})"
        )
