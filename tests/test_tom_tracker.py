"""Tests for ToMTracker — Recursive Theory of Mind belief engine."""

import json
from unittest.mock import AsyncMock

import pytest

from apriori.core.tom_tracker import ToMTracker
from apriori.models.shadow_vector import AttachmentStyle, ShadowVector, SHADOW_VALUE_KEYS


class TestInitialization:
    def test_initialization(self, sample_shadow_a, mock_llm_client) -> None:
        tracker = ToMTracker("agent_a", sample_shadow_a, mock_llm_client)
        assert tracker.agent_id == "agent_a"
        assert tracker.shadow is sample_shadow_a
        state = tracker.get_belief_state()
        assert state.agent_id == "agent_a"
        assert state.turn_number == 0
        assert state.epistemic_models == {}
        assert state.hidden_thought_log == []

    def test_invalid_recursion_depth(self, sample_shadow_a, mock_llm_client) -> None:
        with pytest.raises(ValueError, match="recursion_depth must be 2 or 3"):
            ToMTracker("a", sample_shadow_a, mock_llm_client, recursion_depth=4)

    def test_repr(self, sample_shadow_a, mock_llm_client) -> None:
        tracker = ToMTracker("agent_a", sample_shadow_a, mock_llm_client)
        r = repr(tracker)
        assert "ToMTracker" in r
        assert "agent_a" in r
        assert "L2" in r

    def test_depth_3_allowed(self, sample_shadow_a, mock_llm_client) -> None:
        tracker = ToMTracker("agent_a", sample_shadow_a, mock_llm_client, recursion_depth=3)
        assert tracker._recursion_depth == 3


class TestHiddenThought:
    @pytest.mark.asyncio
    async def test_hidden_thought_returns_correct_keys(
        self, sample_shadow_a, mock_llm_client
    ) -> None:
        tracker = ToMTracker("agent_a", sample_shadow_a, mock_llm_client)
        result = await tracker.hidden_thought(
            "agent_b",
            "I really need to feel secure about us.",
            [{"agent": "agent_b", "content": "I really need to feel secure about us."}],
        )
        expected_keys = {
            "agent", "timestamp", "turn", "other_id",
            "l1_update", "l2_projection",
            "epistemic_divergence", "collapse_risk",
            "raw_thought", "recommended_strategy",
        }
        assert set(result.keys()) == expected_keys
        assert result["agent"] == "agent_a"
        assert result["other_id"] == "agent_b"
        assert isinstance(result["epistemic_divergence"], float)
        assert result["collapse_risk"] in ("CRITICAL", "HIGH", "MODERATE", "LOW")

    @pytest.mark.asyncio
    async def test_thought_log_grows_per_turn(
        self, sample_shadow_a, mock_llm_client
    ) -> None:
        tracker = ToMTracker("agent_a", sample_shadow_a, mock_llm_client)
        history = [{"agent": "agent_b", "content": "hello"}]

        await tracker.hidden_thought("agent_b", "hello", history)
        assert len(tracker.get_thought_log()) == 1

        await tracker.hidden_thought("agent_b", "how are you?", history)
        assert len(tracker.get_thought_log()) == 2

        await tracker.hidden_thought("agent_b", "I'm worried.", history)
        assert len(tracker.get_thought_log()) == 3

    @pytest.mark.asyncio
    async def test_l2_differs_from_l0(
        self, sample_shadow_a, mock_llm_client
    ) -> None:
        """What I perform != who I am — L2 projection should differ from L0."""
        tracker = ToMTracker("agent_a", sample_shadow_a, mock_llm_client)
        result = await tracker.hidden_thought(
            "agent_b", "Tell me about yourself.", [{"agent": "agent_b", "content": "Tell me about yourself."}],
        )
        l2 = result["l2_projection"]
        l0 = sample_shadow_a.values
        # At least some dimensions should differ (mock returns different values)
        differences = sum(1 for k in SHADOW_VALUE_KEYS if abs(l2[k] - l0[k]) > 0.01)
        assert differences > 0


class TestBayesianUpdate:
    def test_bayesian_update_clamps_to_range(
        self, sample_shadow_a, mock_llm_client
    ) -> None:
        tracker = ToMTracker("agent_a", sample_shadow_a, mock_llm_client)
        prior = {k: 0.95 for k in SHADOW_VALUE_KEYS}
        likelihood = {k: 0.3 for k in SHADOW_VALUE_KEYS}
        posterior = tracker._bayesian_update(prior, likelihood, confidence=1.0)
        for val in posterior.values():
            assert 0.0 <= val <= 1.0

    def test_zero_confidence_no_update(
        self, sample_shadow_a, mock_llm_client
    ) -> None:
        tracker = ToMTracker("agent_a", sample_shadow_a, mock_llm_client)
        prior = {k: 0.5 for k in SHADOW_VALUE_KEYS}
        likelihood = {k: 0.2 for k in SHADOW_VALUE_KEYS}
        posterior = tracker._bayesian_update(prior, likelihood, confidence=0.0)
        for k in SHADOW_VALUE_KEYS:
            assert posterior[k] == pytest.approx(0.5)

    def test_positive_likelihood_increases_values(
        self, sample_shadow_a, mock_llm_client
    ) -> None:
        tracker = ToMTracker("agent_a", sample_shadow_a, mock_llm_client)
        prior = {k: 0.5 for k in SHADOW_VALUE_KEYS}
        likelihood = {k: 0.2 for k in SHADOW_VALUE_KEYS}
        posterior = tracker._bayesian_update(prior, likelihood, confidence=0.7)
        for k in SHADOW_VALUE_KEYS:
            assert posterior[k] > prior[k]

    def test_negative_likelihood_decreases_values(
        self, sample_shadow_a, mock_llm_client
    ) -> None:
        tracker = ToMTracker("agent_a", sample_shadow_a, mock_llm_client)
        prior = {k: 0.5 for k in SHADOW_VALUE_KEYS}
        likelihood = {k: -0.2 for k in SHADOW_VALUE_KEYS}
        posterior = tracker._bayesian_update(prior, likelihood, confidence=0.7)
        for k in SHADOW_VALUE_KEYS:
            assert posterior[k] < prior[k]

    def test_clamps_at_zero(self, sample_shadow_a, mock_llm_client) -> None:
        tracker = ToMTracker("agent_a", sample_shadow_a, mock_llm_client)
        prior = {k: 0.0 for k in SHADOW_VALUE_KEYS}
        likelihood = {k: -0.3 for k in SHADOW_VALUE_KEYS}
        posterior = tracker._bayesian_update(prior, likelihood, confidence=1.0)
        for val in posterior.values():
            assert val == 0.0


class TestKLDivergence:
    def test_kl_divergence_identical_vectors_is_zero(
        self, sample_shadow_a, mock_llm_client
    ) -> None:
        tracker = ToMTracker("agent_a", sample_shadow_a, mock_llm_client)
        values = {k: 0.5 for k in SHADOW_VALUE_KEYS}
        assert tracker._kl_divergence(values, values) == pytest.approx(0.0, abs=1e-6)

    def test_kl_divergence_symmetric(
        self, sample_shadow_a, mock_llm_client
    ) -> None:
        """Jensen-Shannon divergence is symmetric: JSD(P,Q) == JSD(Q,P)."""
        tracker = ToMTracker("agent_a", sample_shadow_a, mock_llm_client)
        p = {"autonomy": 0.8, "security": 0.2, "achievement": 0.5, "intimacy": 0.3,
             "novelty": 0.6, "stability": 0.4, "power": 0.7, "belonging": 0.1}
        q = {"autonomy": 0.3, "security": 0.7, "achievement": 0.4, "intimacy": 0.8,
             "novelty": 0.2, "stability": 0.6, "power": 0.1, "belonging": 0.9}
        jsd_pq = tracker._kl_divergence(p, q)
        jsd_qp = tracker._kl_divergence(q, p)
        assert jsd_pq == pytest.approx(jsd_qp, abs=1e-6)

    def test_kl_divergence_different_vectors_positive(
        self, sample_shadow_a, mock_llm_client
    ) -> None:
        tracker = ToMTracker("agent_a", sample_shadow_a, mock_llm_client)
        # Use non-uniform distributions to get a positive JSD
        keys = sorted(SHADOW_VALUE_KEYS)
        p = {k: 0.9 if i < 4 else 0.1 for i, k in enumerate(keys)}
        q = {k: 0.1 if i < 4 else 0.9 for i, k in enumerate(keys)}
        assert tracker._kl_divergence(p, q) > 0.0


class TestCollapseRiskThresholds:
    def test_collapse_risk_thresholds(
        self, sample_shadow_a, mock_llm_client
    ) -> None:
        tracker = ToMTracker("agent_a", sample_shadow_a, mock_llm_client)
        assert tracker._classify_risk(0.85) == "CRITICAL"
        assert tracker._classify_risk(0.81) == "CRITICAL"
        assert tracker._classify_risk(0.70) == "HIGH"
        assert tracker._classify_risk(0.66) == "HIGH"
        assert tracker._classify_risk(0.50) == "MODERATE"
        assert tracker._classify_risk(0.41) == "MODERATE"
        assert tracker._classify_risk(0.30) == "LOW"
        assert tracker._classify_risk(0.10) == "LOW"


class TestMultipleAgentsIsolated:
    @pytest.mark.asyncio
    async def test_multiple_agents_isolated(
        self, sample_shadow_a, mock_llm_client
    ) -> None:
        """A's model of B doesn't pollute A's model of C."""
        tracker = ToMTracker("agent_a", sample_shadow_a, mock_llm_client)
        history = [{"agent": "agent_b", "content": "I need space."}]

        await tracker.hidden_thought("agent_b", "I need space.", history)
        await tracker.hidden_thought("agent_c", "Let's collaborate!", history)

        state = tracker.get_belief_state()
        assert "agent_b" in state.epistemic_models
        assert "agent_c" in state.epistemic_models

        model_b = state.epistemic_models["agent_b"]
        model_c = state.epistemic_models["agent_c"]

        # Models should have different update counts and potentially different values
        assert model_b.target_agent_id == "agent_b"
        assert model_c.target_agent_id == "agent_c"
        assert model_b.update_count == 1
        assert model_c.update_count == 1


class TestEpistemicGapReport:
    @pytest.mark.asyncio
    async def test_epistemic_gap_report(
        self, sample_shadow_a, mock_llm_client
    ) -> None:
        tracker = ToMTracker("agent_a", sample_shadow_a, mock_llm_client)
        await tracker.hidden_thought(
            "agent_b", "hello", [{"agent": "agent_b", "content": "hello"}],
        )

        report = tracker.get_epistemic_gap_report("agent_b")
        assert "l0_vs_l1" in report
        assert "l1_vs_l2" in report
        assert "l0_vs_l2" in report
        assert "divergence_trend" in report
        assert isinstance(report["l0_l1_total"], float)

    def test_gap_report_unknown_agent(
        self, sample_shadow_a, mock_llm_client
    ) -> None:
        tracker = ToMTracker("agent_a", sample_shadow_a, mock_llm_client)
        report = tracker.get_epistemic_gap_report("unknown")
        assert "error" in report
