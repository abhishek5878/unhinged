import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from apriori.core.tom_tracker import ToMTracker
from apriori.models.shadow_vector import SHADOW_VALUE_KEYS, ShadowVector


class _FakeLLMResponse:
    def __init__(self, content: str) -> None:
        self.content = content


def _make_llm_mock(responses: list[dict] | None = None) -> AsyncMock:
    """Create a mock LLM client that returns JSON responses."""
    mock = AsyncMock()
    if responses is None:
        # Default: neutral value deltas + L2 projection + strategy
        neutral = {k: 0.0 for k in sorted(SHADOW_VALUE_KEYS)}
        projection = {k: 0.5 for k in sorted(SHADOW_VALUE_KEYS)}
        strategy = {"strategy": "probe", "rationale": "gather more data"}
        verbalization = "I'm still forming my impression of them."
        side_effects = [
            _FakeLLMResponse(json.dumps(neutral)),      # _infer_values
            _FakeLLMResponse(json.dumps(projection)),    # _project_their_model
            _FakeLLMResponse(verbalization),             # _verbalize
            _FakeLLMResponse(json.dumps(strategy)),      # _recommend_strategy
        ]
        mock.ainvoke = AsyncMock(side_effect=side_effects)
    else:
        mock.ainvoke = AsyncMock(
            side_effect=[_FakeLLMResponse(json.dumps(r)) for r in responses]
        )
    return mock


class TestToMTrackerInit:
    def test_valid_init(self, sample_shadow_a: ShadowVector) -> None:
        llm = _make_llm_mock()
        tracker = ToMTracker("agent_a", sample_shadow_a, llm)
        assert tracker.agent_id == "agent_a"
        assert tracker.shadow is sample_shadow_a
        assert tracker._recursion_depth == 2

    def test_invalid_depth_raises(self, sample_shadow_a: ShadowVector) -> None:
        with pytest.raises(ValueError, match="recursion_depth must be 2 or 3"):
            ToMTracker("a", sample_shadow_a, _make_llm_mock(), recursion_depth=4)

    def test_repr(self, sample_shadow_a: ShadowVector) -> None:
        tracker = ToMTracker("a", sample_shadow_a, _make_llm_mock())
        r = repr(tracker)
        assert "ToMTracker" in r
        assert "agent='a'" in r


class TestBayesianUpdate:
    def test_no_change_with_zero_likelihood(self, sample_shadow_a: ShadowVector) -> None:
        tracker = ToMTracker("a", sample_shadow_a, _make_llm_mock())
        prior = {k: 0.5 for k in SHADOW_VALUE_KEYS}
        likelihood = {k: 0.0 for k in SHADOW_VALUE_KEYS}
        posterior = tracker._bayesian_update(prior, likelihood, confidence=0.7)
        assert posterior == prior

    def test_positive_shift(self, sample_shadow_a: ShadowVector) -> None:
        tracker = ToMTracker("a", sample_shadow_a, _make_llm_mock())
        prior = {k: 0.5 for k in SHADOW_VALUE_KEYS}
        likelihood = {k: 0.0 for k in SHADOW_VALUE_KEYS}
        likelihood["autonomy"] = 0.3
        posterior = tracker._bayesian_update(prior, likelihood, confidence=1.0)
        assert posterior["autonomy"] == pytest.approx(0.8)
        assert posterior["security"] == pytest.approx(0.5)

    def test_clamping(self, sample_shadow_a: ShadowVector) -> None:
        tracker = ToMTracker("a", sample_shadow_a, _make_llm_mock())
        prior = {k: 0.95 for k in SHADOW_VALUE_KEYS}
        likelihood = {k: 0.3 for k in SHADOW_VALUE_KEYS}
        posterior = tracker._bayesian_update(prior, likelihood, confidence=1.0)
        for v in posterior.values():
            assert 0.0 <= v <= 1.0


class TestKLDivergence:
    def test_identical_distributions_is_zero(self, sample_shadow_a: ShadowVector) -> None:
        tracker = ToMTracker("a", sample_shadow_a, _make_llm_mock())
        p = {k: 0.5 for k in SHADOW_VALUE_KEYS}
        assert tracker._kl_divergence(p, p) == pytest.approx(0.0)

    def test_different_distributions_positive(self, sample_shadow_a: ShadowVector) -> None:
        tracker = ToMTracker("a", sample_shadow_a, _make_llm_mock())
        p = {k: 0.5 for k in SHADOW_VALUE_KEYS}
        q = {k: 0.1 for k in SHADOW_VALUE_KEYS}
        q["autonomy"] = 0.9
        assert tracker._kl_divergence(p, q) > 0


class TestRiskClassification:
    def test_levels(self, sample_shadow_a: ShadowVector) -> None:
        tracker = ToMTracker("a", sample_shadow_a, _make_llm_mock())
        assert tracker._classify_risk(0.9) == "CRITICAL"
        assert tracker._classify_risk(0.7) == "HIGH"
        assert tracker._classify_risk(0.5) == "MODERATE"
        assert tracker._classify_risk(0.2) == "LOW"


class TestHiddenThought:
    @pytest.mark.asyncio
    async def test_hidden_thought_returns_expected_keys(
        self, sample_shadow_a: ShadowVector
    ) -> None:
        llm = _make_llm_mock()
        tracker = ToMTracker("a", sample_shadow_a, llm)

        result = await tracker.hidden_thought(
            "b",
            "I really need my own space right now.",
            [{"agent": "b", "content": "I really need my own space right now."}],
        )

        expected_keys = {
            "agent", "timestamp", "turn", "other_id",
            "l1_update", "l2_projection", "epistemic_divergence",
            "collapse_risk", "raw_thought", "recommended_strategy",
        }
        assert set(result.keys()) == expected_keys
        assert result["agent"] == "a"
        assert result["other_id"] == "b"
        assert result["turn"] == 1

    @pytest.mark.asyncio
    async def test_thought_log_grows(self, sample_shadow_a: ShadowVector) -> None:
        neutral = {k: 0.0 for k in sorted(SHADOW_VALUE_KEYS)}
        projection = {k: 0.5 for k in sorted(SHADOW_VALUE_KEYS)}
        strategy = {"strategy": "probe", "rationale": "test"}

        # Need 4 responses per call (infer, project, verbalize, strategy)
        responses = []
        for _ in range(2):
            responses.extend([
                _FakeLLMResponse(json.dumps(neutral)),
                _FakeLLMResponse(json.dumps(projection)),
                _FakeLLMResponse("thinking..."),
                _FakeLLMResponse(json.dumps(strategy)),
            ])

        llm = AsyncMock()
        llm.ainvoke = AsyncMock(side_effect=responses)
        tracker = ToMTracker("a", sample_shadow_a, llm)

        await tracker.hidden_thought("b", "hi", [])
        await tracker.hidden_thought("b", "hello", [])

        assert len(tracker.get_thought_log()) == 2


class TestEpistemicGapReport:
    @pytest.mark.asyncio
    async def test_report_after_thought(self, sample_shadow_a: ShadowVector) -> None:
        llm = _make_llm_mock()
        tracker = ToMTracker("a", sample_shadow_a, llm)

        await tracker.hidden_thought("b", "test", [])
        report = tracker.get_epistemic_gap_report("b")

        assert "l0_vs_l1" in report
        assert "l1_vs_l2" in report
        assert "divergence_trend" in report

    def test_report_no_model(self, sample_shadow_a: ShadowVector) -> None:
        tracker = ToMTracker("a", sample_shadow_a, _make_llm_mock())
        report = tracker.get_epistemic_gap_report("unknown")
        assert "error" in report
