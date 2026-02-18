"""Tests for StochasticEventGenerator — Precision chaos engine."""

import json
from unittest.mock import AsyncMock

import pytest

from apriori.core.event_generator import StochasticEventGenerator
from apriori.models.events import EventTaxonomy
from apriori.models.shadow_vector import AttachmentStyle, ShadowVector, SHADOW_VALUE_KEYS
from conftest import FakeLLMResponse


def _make_uniform_shadow(agent_id: str, **overrides) -> ShadowVector:
    """Create a shadow with uniform 0.5 values and optional overrides."""
    kwargs = {
        "agent_id": agent_id,
        "values": {k: 0.5 for k in SHADOW_VALUE_KEYS},
        "attachment_style": AttachmentStyle.SECURE,
        "fear_architecture": [],
        "linguistic_signature": [],
        "entropy_tolerance": 0.5,
        "communication_style": "direct",
    }
    kwargs.update(overrides)
    return ShadowVector(**kwargs)


class TestInit:
    def test_valid_distributions(self, mock_llm_client) -> None:
        for dist in ("pareto", "uniform", "beta"):
            gen = StochasticEventGenerator(mock_llm_client, severity_distribution=dist)
            assert gen._severity_distribution == dist

    def test_invalid_distribution_raises(self, mock_llm_client) -> None:
        with pytest.raises(ValueError, match="severity_distribution"):
            StochasticEventGenerator(mock_llm_client, severity_distribution="invalid")

    def test_repr(self, mock_llm_client) -> None:
        gen = StochasticEventGenerator(mock_llm_client)
        assert "pareto" in repr(gen)


class TestSharedVulnerability:
    def test_shared_vulnerability_identifies_max(
        self, sample_shadow_a, sample_shadow_b, mock_llm_client
    ) -> None:
        gen = StochasticEventGenerator(mock_llm_client)
        axis, score, explanation = gen.identify_shared_vulnerability(
            sample_shadow_a, sample_shadow_b,
        )
        assert isinstance(axis, str)
        assert axis in SHADOW_VALUE_KEYS
        assert isinstance(score, float)
        assert score > 0
        assert isinstance(explanation, str)

    def test_attachment_amplification_anxious_avoidant(self, mock_llm_client) -> None:
        """Anxious+Avoidant pair should get 1.6x amplification on intimacy."""
        shadow_a = _make_uniform_shadow(
            "a", attachment_style=AttachmentStyle.ANXIOUS,
        )
        shadow_b = _make_uniform_shadow(
            "b", attachment_style=AttachmentStyle.AVOIDANT,
        )
        gen = StochasticEventGenerator(mock_llm_client)
        axis, score, _ = gen.identify_shared_vulnerability(shadow_a, shadow_b)
        assert axis == "intimacy"
        assert score == pytest.approx(0.25 * 1.6)

    def test_shared_fear_boost(self, mock_llm_client) -> None:
        """When agents share a fear, the corresponding axis gets 1.4x boost."""
        shadow_a = _make_uniform_shadow(
            "a", fear_architecture=["abandonment"],
        )
        shadow_b = _make_uniform_shadow(
            "b", fear_architecture=["abandonment"],
        )
        gen = StochasticEventGenerator(mock_llm_client)
        axis, score, _ = gen.identify_shared_vulnerability(shadow_a, shadow_b)
        assert axis == "belonging"
        assert score == pytest.approx(0.5 * 0.5 * 1.4)


class TestSeveritySampling:
    def test_pareto_severity_heavy_tail(self, mock_llm_client) -> None:
        """>60% of Pareto samples should be below 0.4 (realistic distribution)."""
        gen = StochasticEventGenerator(mock_llm_client, pareto_alpha=1.5)
        samples = [gen._sample_severity(1.0) for _ in range(500)]
        below_04 = sum(1 for s in samples if s < 0.4)
        assert below_04 / 500 > 0.60

    def test_clamped_range(self, mock_llm_client) -> None:
        gen = StochasticEventGenerator(mock_llm_client, pareto_alpha=1.0)
        for _ in range(200):
            s = gen._sample_severity(1.0)
            assert 0.05 <= s <= 0.98

    def test_uniform_distribution(self, mock_llm_client) -> None:
        gen = StochasticEventGenerator(mock_llm_client, severity_distribution="uniform")
        samples = [gen._sample_severity(1.0) for _ in range(200)]
        assert all(0.05 <= s <= 0.98 for s in samples)

    def test_beta_distribution(self, mock_llm_client) -> None:
        gen = StochasticEventGenerator(mock_llm_client, severity_distribution="beta")
        samples = [gen._sample_severity(1.0) for _ in range(200)]
        assert all(0.05 <= s <= 0.98 for s in samples)


class TestBlackSwanGeneration:
    @pytest.mark.asyncio
    async def test_black_swan_fields_complete(
        self, sample_shadow_a, sample_shadow_b, mock_llm_client
    ) -> None:
        gen = StochasticEventGenerator(mock_llm_client)
        event = await gen.generate_black_swan(
            sample_shadow_a, sample_shadow_b, severity_override=0.5, seed=42,
        )
        assert 0.0 <= event.severity <= 1.0
        assert event.narrative_description
        assert event.decision_point
        assert event.target_vulnerability_axis in SHADOW_VALUE_KEYS
        assert isinstance(event.expected_collapse_vector, dict)
        assert isinstance(event.elasticity_threshold, float)

    @pytest.mark.asyncio
    async def test_generate_narrative_called_once_per_event(
        self, sample_shadow_a, sample_shadow_b, mock_llm_client
    ) -> None:
        gen = StochasticEventGenerator(mock_llm_client)
        mock_llm_client.ainvoke.reset_mock()
        await gen.generate_black_swan(
            sample_shadow_a, sample_shadow_b, severity_override=0.5, seed=1,
        )
        # Only one LLM call should be made (for narrative generation)
        assert mock_llm_client.ainvoke.call_count == 1


class TestElasticityThreshold:
    def test_elasticity_threshold_lower_for_secure(self, mock_llm_client) -> None:
        """Secure attachment pairs should have lower threshold (more resilient)."""
        secure_a = _make_uniform_shadow(
            "a", attachment_style=AttachmentStyle.SECURE, entropy_tolerance=0.8,
        )
        secure_b = _make_uniform_shadow(
            "b", attachment_style=AttachmentStyle.SECURE, entropy_tolerance=0.8,
        )
        anxious_a = _make_uniform_shadow(
            "a", attachment_style=AttachmentStyle.ANXIOUS, entropy_tolerance=0.2,
        )
        anxious_b = _make_uniform_shadow(
            "b", attachment_style=AttachmentStyle.ANXIOUS, entropy_tolerance=0.2,
        )
        gen = StochasticEventGenerator(mock_llm_client)
        t_secure = gen._compute_elasticity_threshold(secure_a, secure_b)
        t_anxious = gen._compute_elasticity_threshold(anxious_a, anxious_b)
        assert t_secure < t_anxious


class TestCascade:
    @pytest.mark.asyncio
    async def test_cascade_severity_decreases(
        self, sample_shadow_a, sample_shadow_b, mock_llm_client
    ) -> None:
        """Each aftershock should have lower severity than the primary."""
        gen = StochasticEventGenerator(mock_llm_client)
        primary = await gen.generate_black_swan(
            sample_shadow_a, sample_shadow_b, severity_override=0.7,
        )
        cascade = await gen.run_cascade(
            primary, sample_shadow_a, sample_shadow_b, n_aftershocks=3,
        )
        assert len(cascade) == 4  # primary + 3 aftershocks
        assert cascade[0] is primary
        for aftershock in cascade[1:]:
            assert aftershock.severity < primary.severity


class TestCollapseVector:
    def test_predict_collapse_vector(
        self, sample_shadow_a, sample_shadow_b, mock_llm_client
    ) -> None:
        result = StochasticEventGenerator._predict_collapse_vector(
            sample_shadow_a, sample_shadow_b, "security", 0.8,
        )
        assert sample_shadow_a.agent_id in result
        assert sample_shadow_b.agent_id in result
        assert all(v >= 0 for v in result.values())
