from __future__ import annotations

from typing import Any

from apriori.models.shadow_vector import BeliefState, ShadowVector


class BaseRelationalAgent:
    """Base class for relational agents — a LangGraph node.

    Each agent maintains 4 simultaneous state layers:
    - L0: ShadowVector (ground truth, never exposed)
    - L1: Projected epistemic model of other agent
    - L2: Meta-epistemic projection
    - L3: Fourth-order recursive loop (optional, depth-gated)
    """

    def __init__(self, shadow: ShadowVector) -> None:
        self._shadow = shadow
        self._belief_state: BeliefState | None = None

    async def respond(self, state: dict[str, Any]) -> dict[str, Any]:
        """LangGraph node entrypoint — generate a response given graph state."""
        pass

    async def update_beliefs(self, observation: dict[str, Any]) -> None:
        """Update epistemic models based on dialogue observation."""
        pass

    def get_hidden_thought(self) -> str:
        """Generate internal monologue (never exposed to other agent)."""
        pass
