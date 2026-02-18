"""Shared test fixtures for the APRIORI test suite."""

from __future__ import annotations

import json
from typing import Optional
from unittest.mock import AsyncMock

import pytest

from apriori.models.shadow_vector import AttachmentStyle, ShadowVector


class FakeLLMResponse:
    """Mock LLM response object with .content attribute."""

    def __init__(self, content: str) -> None:
        self.content = content


@pytest.fixture
def sample_shadow_a() -> ShadowVector:
    """Anxious attachment, high financial anxiety, Hinglish takiya-kalaam."""
    return ShadowVector(
        agent_id="agent_a",
        values={
            "autonomy": 0.6,
            "security": 0.3,
            "achievement": 0.8,
            "intimacy": 0.7,
            "novelty": 0.5,
            "stability": 0.2,
            "power": 0.4,
            "belonging": 0.6,
        },
        attachment_style=AttachmentStyle.ANXIOUS,
        fear_architecture=["abandonment", "failure"],
        linguistic_signature=["sorted scene", "it's a vibe", "full filmy"],
        entropy_tolerance=0.4,
        communication_style="indirect",
    )


@pytest.fixture
def sample_shadow_b() -> ShadowVector:
    """Avoidant attachment, high achievement drive, Hinglish takiya-kalaam."""
    return ShadowVector(
        agent_id="agent_b",
        values={
            "autonomy": 0.7,
            "security": 0.5,
            "achievement": 0.9,
            "intimacy": 0.3,
            "novelty": 0.6,
            "stability": 0.8,
            "power": 0.5,
            "belonging": 0.4,
        },
        attachment_style=AttachmentStyle.AVOIDANT,
        fear_architecture=["engulfment", "vulnerability"],
        linguistic_signature=["pakka", "bindaas", "ekdum solid"],
        entropy_tolerance=0.6,
        communication_style="direct",
    )


def _make_value_deltas(overrides: Optional[dict] = None) -> dict:
    """Generate a neutral value delta dict with optional overrides."""
    base = {k: 0.0 for k in [
        "autonomy", "security", "achievement", "intimacy",
        "novelty", "stability", "power", "belonging",
    ]}
    if overrides:
        base.update(overrides)
    return base


def _make_l2_values(overrides: Optional[dict] = None) -> dict:
    """Generate neutral L2 values with optional overrides."""
    base = {k: 0.5 for k in [
        "autonomy", "security", "achievement", "intimacy",
        "novelty", "stability", "power", "belonging",
    ]}
    if overrides:
        base.update(overrides)
    return base


@pytest.fixture
def mock_llm_client() -> AsyncMock:
    """Mock LLM that returns structured JSON responses based on prompt content.

    Handles: value inference, L2 projection, L3 loop, strategy,
    defensive attribution, narrative incoherence, verbalization, crisis narrative.
    """
    mock = AsyncMock()

    responses = {
        "value_deltas": json.dumps(_make_value_deltas({"intimacy": 0.1, "security": -0.05})),
        "l2_projection": json.dumps(_make_l2_values({"autonomy": 0.6, "intimacy": 0.4})),
        "l3_projection": json.dumps(_make_l2_values()),
        "strategy": json.dumps({"strategy": "probe", "rationale": "Gather more information."}),
        "defensive": json.dumps({"score": 0.1, "evidence": "No blame patterns detected."}),
        "narrative": json.dumps({"score": 0.1, "has_future_statements": True, "evidence": "Shared narrative intact."}),
        "verbalize": "I sense a gap between who I really am and what they see. The divergence is low but worth monitoring.",
        "crisis_narrative": json.dumps({
            "narrative": "A financial crisis emerged unexpectedly. The startup they invested in collapsed.",
            "decision_point": "They must decide whether to face the fallout together or separately.",
            "likely_a_reaction": "Agent A panics and seeks reassurance immediately.",
            "likely_b_reaction": "Agent B withdraws to process alone.",
        }),
    }

    def _decide_response(prompt, **kwargs) -> FakeLLMResponse:
        text = str(prompt).lower() if not isinstance(prompt, str) else prompt.lower()

        if "defensive attribution" in text or "blame" in text:
            return FakeLLMResponse(responses["defensive"])
        if "narrative coherence" in text or "narrative incoherence" in text:
            return FakeLLMResponse(responses["narrative"])
        if "crisis scenario" in text or "realistic crisis" in text:
            return FakeLLMResponse(responses["crisis_narrative"])
        if "strategy" in text and "rationale" in text:
            return FakeLLMResponse(responses["strategy"])
        if "fourth-order" in text or "l3" in text:
            return FakeLLMResponse(responses["l3_projection"])
        if "projected persona" in text or "likely believes" in text:
            return FakeLLMResponse(responses["l2_projection"])
        if "inner voice" in text or "inner monologue" in text:
            return FakeLLMResponse(responses["verbalize"])
        if "implied importance shift" in text or "value dimension" in text:
            return FakeLLMResponse(responses["value_deltas"])

        return FakeLLMResponse(responses["value_deltas"])

    mock.ainvoke = AsyncMock(side_effect=_decide_response)
    return mock
