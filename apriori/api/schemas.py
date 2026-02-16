from __future__ import annotations

from pydantic import BaseModel, Field

from apriori.models.shadow_vector import ShadowVector


class SimulationRequest(BaseModel):
    pair_id: str
    shadow_a: ShadowVector
    shadow_b: ShadowVector
    n_simulations: int = Field(default=100, ge=1, le=10000)
    max_turns: int = Field(default=50, ge=1, le=500)


class SimulationResponse(BaseModel):
    simulation_id: str
    status: str = "queued"


class SimulationResultResponse(BaseModel):
    simulation_id: str
    status: str
    result: dict | None = None


class ProfileCreateRequest(BaseModel):
    shadow: ShadowVector


class ProfileResponse(BaseModel):
    agent_id: str
    shadow: ShadowVector
