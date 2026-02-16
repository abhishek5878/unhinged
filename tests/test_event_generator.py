import json
from unittest.mock import AsyncMock

import pytest

from apriori.core.event_generator import StochasticEventGenerator
from apriori.models.events import EventTaxonomy
from apriori.models.shadow_vector import AttachmentStyle, ShadowVector


class _FakeLLMResponse:
    def __init__(self, content: str) -> None:
        self.content = content


def _make_llm() -> AsyncMock:
    narrative = {
        "narrative": "A crisis occurred. It was unexpected. Everything changed.",
        "decision_point": "They must decide whether to face it together or apart.",
        "likely_a_reaction": "Agent A freezes, unsure how to respond.",
        "likely_b_reaction": "Agent B retreats into silence.",
    }
    mock = AsyncMock()
    mock.ainvoke = AsyncMock(return_value=_FakeLLMResponse(json.dumps(narrative)))
    return mock


class TestInit:
    def test_valid_distributions(self) -> None:
        for dist in ("pareto", "uniform", "beta"):
            gen = StochasticEventGenerator(_make_llm(), severity_distribution=dist)
            assert gen._severity_distribution == dist

    def test_invalid_distribution_raises(self) -> None:
        with pytest.raises(ValueError, match="severity_distribution"):
            StochasticEventGenerator(_make_llm(), severity_distribution="invalid")

    def test_repr(self) -> None:
        gen = StochasticEventGenerator(_make_llm())
        assert "pareto" in repr(gen)


class TestIdentifySharedVulnerability:
    def test_returns_tuple(
        self, sample_shadow_a: ShadowVector, sample_shadow_b: ShadowVector
    ) -> None:
        gen = StochasticEventGenerator(_make_llm())
        axis, score, explanation = gen.identify_shared_vulnerability(
            sample_shadow_a, sample_shadow_b
        )
        assert isinstance(axis, str)
        assert isinstance(score, float)
        assert score > 0
        assert isinstance(explanation, str)

    def test_shared_fear_boost(self) -> None:
        """When agents share a fear, the corresponding axis should get a 1.4x boost."""
        base_values = {
            "autonomy": 0.5, "security": 0.5, "achievement": 0.5, "intimacy": 0.5,
            "novelty": 0.5, "stability": 0.5, "power": 0.5, "belonging": 0.5,
        }
        shadow_a = ShadowVector(
            agent_id="a", values=dict(base_values),
            attachment_style=AttachmentStyle.SECURE,
            fear_architecture=["abandonment"],
            linguistic_signature=[], entropy_tolerance=0.5,
            communication_style="direct",
        )
        shadow_b = ShadowVector(
            agent_id="b", values=dict(base_values),
            attachment_style=AttachmentStyle.SECURE,
            fear_architecture=["abandonment"],
            linguistic_signature=[], entropy_tolerance=0.5,
            communication_style="direct",
        )
        gen = StochasticEventGenerator(_make_llm())
        axis, score, _ = gen.identify_shared_vulnerability(shadow_a, shadow_b)
        # "abandonment" maps to "belonging"; with equal base values and 1.4x boost,
        # belonging should be the top axis
        assert axis == "belonging"
        assert score == pytest.approx(0.5 * 0.5 * 1.4)

    def test_anxious_avoidant_amplification(self) -> None:
        """Anxious+Avoidant pair should get 1.6x amplification on intimacy."""
        base_values = {
            "autonomy": 0.5, "security": 0.5, "achievement": 0.5, "intimacy": 0.5,
            "novelty": 0.5, "stability": 0.5, "power": 0.5, "belonging": 0.5,
        }
        shadow_a = ShadowVector(
            agent_id="a", values=dict(base_values),
            attachment_style=AttachmentStyle.ANXIOUS,
            fear_architecture=[], linguistic_signature=[],
            entropy_tolerance=0.5, communication_style="direct",
        )
        shadow_b = ShadowVector(
            agent_id="b", values=dict(base_values),
            attachment_style=AttachmentStyle.AVOIDANT,
            fear_architecture=[], linguistic_signature=[],
            entropy_tolerance=0.5, communication_style="direct",
        )
        gen = StochasticEventGenerator(_make_llm())
        axis, score, _ = gen.identify_shared_vulnerability(shadow_a, shadow_b)
        assert axis == "intimacy"
        assert score == pytest.approx(0.25 * 1.6)


class TestSampleSeverity:
    def test_clamped_range(self) -> None:
        gen = StochasticEventGenerator(_make_llm(), pareto_alpha=1.0)
        for _ in range(100):
            s = gen._sample_severity(1.0)
            assert 0.05 <= s <= 0.98

    def test_uniform_distribution(self) -> None:
        gen = StochasticEventGenerator(_make_llm(), severity_distribution="uniform")
        samples = [gen._sample_severity(1.0) for _ in range(200)]
        assert all(0.05 <= s <= 0.98 for s in samples)

    def test_beta_distribution(self) -> None:
        gen = StochasticEventGenerator(_make_llm(), severity_distribution="beta")
        samples = [gen._sample_severity(1.0) for _ in range(200)]
        assert all(0.05 <= s <= 0.98 for s in samples)


class TestElasticityThreshold:
    def test_secure_pair_lower_threshold(self) -> None:
        base = {
            "autonomy": 0.5, "security": 0.5, "achievement": 0.5, "intimacy": 0.5,
            "novelty": 0.5, "stability": 0.5, "power": 0.5, "belonging": 0.5,
        }
        secure_a = ShadowVector(
            agent_id="a", values=dict(base),
            attachment_style=AttachmentStyle.SECURE,
            fear_architecture=[], linguistic_signature=[],
            entropy_tolerance=0.8, communication_style="direct",
        )
        secure_b = ShadowVector(
            agent_id="b", values=dict(base),
            attachment_style=AttachmentStyle.SECURE,
            fear_architecture=[], linguistic_signature=[],
            entropy_tolerance=0.8, communication_style="direct",
        )
        anxious_a = ShadowVector(
            agent_id="a", values=dict(base),
            attachment_style=AttachmentStyle.ANXIOUS,
            fear_architecture=[], linguistic_signature=[],
            entropy_tolerance=0.2, communication_style="indirect",
        )
        anxious_b = ShadowVector(
            agent_id="b", values=dict(base),
            attachment_style=AttachmentStyle.ANXIOUS,
            fear_architecture=[], linguistic_signature=[],
            entropy_tolerance=0.2, communication_style="indirect",
        )
        gen = StochasticEventGenerator(_make_llm())
        t_secure = gen._compute_elasticity_threshold(secure_a, secure_b)
        t_anxious = gen._compute_elasticity_threshold(anxious_a, anxious_b)
        assert t_secure < t_anxious


class TestGenerateBlackSwan:
    @pytest.mark.asyncio
    async def test_generates_valid_event(
        self, sample_shadow_a: ShadowVector, sample_shadow_b: ShadowVector
    ) -> None:
        gen = StochasticEventGenerator(_make_llm())
        event = await gen.generate_black_swan(
            sample_shadow_a, sample_shadow_b, severity_override=0.5, seed=42
        )
        assert 0.0 <= event.severity <= 1.0
        assert event.narrative_description
        assert event.decision_point
        assert event.target_vulnerability_axis in {
            "autonomy", "security", "achievement", "intimacy",
            "novelty", "stability", "power", "belonging",
        }


class TestCollapseVector:
    def test_predict_collapse_vector(
        self, sample_shadow_a: ShadowVector, sample_shadow_b: ShadowVector
    ) -> None:
        result = StochasticEventGenerator._predict_collapse_vector(
            sample_shadow_a, sample_shadow_b, "security", 0.8
        )
        assert sample_shadow_a.agent_id in result
        assert sample_shadow_b.agent_id in result
        assert all(v >= 0 for v in result.values())


class TestRunCascade:
    @pytest.mark.asyncio
    async def test_cascade_length(
        self, sample_shadow_a: ShadowVector, sample_shadow_b: ShadowVector
    ) -> None:
        gen = StochasticEventGenerator(_make_llm())
        primary = await gen.generate_black_swan(
            sample_shadow_a, sample_shadow_b, severity_override=0.7
        )
        cascade = await gen.run_cascade(primary, sample_shadow_a, sample_shadow_b, n_aftershocks=3)
        assert len(cascade) == 4  # primary + 3 aftershocks
        assert cascade[0] is primary
