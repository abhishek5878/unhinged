from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class LinguisticProfile(BaseModel):
    """Linguistic fingerprint of an agent, tracking code-switching and convergence."""

    agent_id: str
    primary_language: str = Field(default="hinglish", description="Primary language mode")
    code_switch_rate: float = Field(
        ..., ge=0.0, le=1.0, description="Frequency of language switching per utterance"
    )
    formality_index: float = Field(
        ..., ge=0.0, le=1.0, description="0=casual, 1=formal"
    )
    avg_utterance_length: float = Field(..., ge=0.0, description="Mean token count")
    takiya_kalaam: List[str] = Field(
        default_factory=list, description="Signature phrases / verbal tics"
    )
    emotional_lexicon_density: float = Field(
        ..., ge=0.0, le=1.0, description="Proportion of emotion-bearing tokens"
    )
    hedge_rate: float = Field(
        ..., ge=0.0, le=1.0, description="Rate of hedging expressions"
    )
    indic_bert_embedding: Optional[List[float]] = Field(
        default=None, description="indic-bert CLS embedding of aggregated speech"
    )
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("takiya_kalaam")
    @classmethod
    def validate_takiya_kalaam(cls, v: List[str]) -> List[str]:
        return [phrase.strip() for phrase in v if phrase.strip()]

    def __repr__(self) -> str:
        return (
            f"LinguisticProfile(agent={self.agent_id!r}, "
            f"lang={self.primary_language!r}, "
            f"cs_rate={self.code_switch_rate:.2f}, "
            f"formality={self.formality_index:.2f})"
        )


class ConvergenceRecord(BaseModel):
    """Tracks linguistic convergence between two agents over time."""

    pair_id: str
    agent_a_id: str
    agent_b_id: str
    turn_number: int = Field(..., ge=0)
    cosine_similarity: float = Field(
        ..., ge=-1.0, le=1.0, description="Embedding-space cosine similarity"
    )
    code_switch_delta: float = Field(
        ..., description="Difference in code-switch rates (a - b)"
    )
    formality_delta: float = Field(
        ..., description="Difference in formality indices (a - b)"
    )
    lexical_overlap: float = Field(
        ..., ge=0.0, le=1.0, description="Jaccard similarity of vocabulary"
    )
    convergence_velocity: float = Field(
        ..., description="Rate of convergence change per turn (positive = converging)"
    )
    mutual_adaptation_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Symmetric measure of bidirectional linguistic accommodation",
    )
    snapshot_profiles: Dict[str, LinguisticProfile] = Field(
        ..., description="Keyed by agent_id — profiles at this turn"
    )
    recorded_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("snapshot_profiles")
    @classmethod
    def validate_snapshot_profiles(cls, v: Dict[str, LinguisticProfile]) -> Dict[str, LinguisticProfile]:
        if len(v) != 2:
            raise ValueError("snapshot_profiles must contain exactly 2 agent profiles")
        return v

    def __repr__(self) -> str:
        direction = "converging" if self.convergence_velocity > 0 else "diverging"
        return (
            f"ConvergenceRecord(pair={self.pair_id!r}, "
            f"turn={self.turn_number}, "
            f"cos_sim={self.cosine_similarity:.3f}, "
            f"{direction})"
        )
