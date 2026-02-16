from __future__ import annotations

from fastapi import APIRouter

from apriori.api.schemas import SimulationRequest, SimulationResponse, SimulationResultResponse

router = APIRouter()


@router.post("", response_model=SimulationResponse)
async def create_simulation(request: SimulationRequest) -> SimulationResponse:
    """Launch a new Monte Carlo relational simulation."""
    pass


@router.get("/results/{simulation_id}", response_model=SimulationResultResponse)
async def get_simulation_result(simulation_id: str) -> SimulationResultResponse:
    """Retrieve results for a completed simulation."""
    pass
