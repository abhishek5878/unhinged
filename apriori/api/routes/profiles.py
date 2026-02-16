from __future__ import annotations

from fastapi import APIRouter

from apriori.api.schemas import ProfileCreateRequest, ProfileResponse

router = APIRouter()


@router.post("", response_model=ProfileResponse)
async def create_profile(request: ProfileCreateRequest) -> ProfileResponse:
    """Create a new agent shadow vector profile."""
    pass


@router.get("/{agent_id}", response_model=ProfileResponse)
async def get_profile(agent_id: str) -> ProfileResponse:
    """Retrieve an agent's shadow vector profile."""
    pass


@router.put("/{agent_id}", response_model=ProfileResponse)
async def update_profile(agent_id: str, request: ProfileCreateRequest) -> ProfileResponse:
    """Update an agent's shadow vector profile."""
    pass


@router.delete("/{agent_id}")
async def delete_profile(agent_id: str) -> dict:
    """Delete an agent's shadow vector profile."""
    pass
