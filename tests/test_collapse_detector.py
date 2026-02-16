import json
from unittest.mock import AsyncMock

import pytest

from apriori.core.alignment_scorer import LinguisticAlignmentScorer
from apriori.core.collapse_detector import BeliefCollapseDetector
from apriori.core.tom_tracker import ToMTracker
from apriori.models.shadow_vector import AttachmentStyle, ShadowVector, SHADOW_VALUE_KEYS


class _FakeLLMResponse:
    def __init__(self, content: str) -> None:
        self.content = content


def _make_shadow(agent_id: str) -> ShadowVector:
    return ShadowVector(
        agent_id=agent_id,
        values={k: 0.5 for k in SHADOW_VALUE_KEYS},
        attachment_style=AttachmentStyle.SECURE,
        fear_architecture=[],
        linguistic_signature=[],
        entropy_tolerance=0.5,
        communication_style="direct",
    )


def _make_llm_for_detector() -> AsyncMock:
    """LLM mock that returns low scores for defensive attribution and incoherence."""
    mock = AsyncMock()
    mock.ainvoke = AsyncMock(
        return_value=_FakeLLMResponse(json.dumps({"score": 0.1, "evidence": "test", "has_future_statements": True}))
    )
    return mock


def _make_llm_for_tracker() -> AsyncMock:
    """LLM mock for ToMTracker init (won't be called in these tests)."""
    return AsyncMock()


def _make_detector() -> BeliefCollapseDetector:
    shadow_a = _make_shadow("a")
    shadow_b = _make_shadow("b")
    llm_tracker = _make_llm_for_tracker()
    tom_a = ToMTracker("a", shadow_a, llm_tracker)
    tom_b = ToMTracker("b", shadow_b, llm_tracker)
    scorer = LinguisticAlignmentScorer()
    llm_detector = _make_llm_for_detector()
    return BeliefCollapseDetector(tom_a, tom_b, scorer, llm_detector)


class TestBeliefCollapseDetectorInit:
    def test_signal_weights_sum_to_one(self) -> None:
        total = sum(BeliefCollapseDetector.COLLAPSE_SIGNALS.values())
        assert total == pytest.approx(1.0)

    def test_repr(self) -> None:
        detector = _make_detector()
        r = repr(detector)
        assert "BeliefCollapseDetector" in r
        assert "'a'" in r
        assert "'b'" in r


class TestRiskClassification:
    def test_all_levels(self) -> None:
        assert BeliefCollapseDetector._classify_risk_level(0.95) == "CRITICAL"
        assert BeliefCollapseDetector._classify_risk_level(0.70) == "HIGH"
        assert BeliefCollapseDetector._classify_risk_level(0.50) == "MODERATE"
        assert BeliefCollapseDetector._classify_risk_level(0.25) == "LOW"
        assert BeliefCollapseDetector._classify_risk_level(0.10) == "STABLE"


class TestResponseLengthProxy:
    def test_no_change(self) -> None:
        detector = _make_detector()
        history = [{"content": "x" * 100}] * 20
        assert detector._response_length_proxy(history) == pytest.approx(0.0)

    def test_terse_responses(self) -> None:
        detector = _make_detector()
        history = [{"content": "x" * 100}] * 10 + [{"content": "ok"}] * 5
        score = detector._response_length_proxy(history)
        assert score > 0.5

    def test_too_short_history(self) -> None:
        detector = _make_detector()
        history = [{"content": "hi"}] * 5
        assert detector._response_length_proxy(history) == 0.0


class TestSuggestIntervention:
    def test_epistemic_critical(self) -> None:
        detector = _make_detector()
        result = detector.suggest_intervention({
            "primary_driver": "epistemic_divergence",
            "risk_level": "CRITICAL",
        })
        assert result == "reanchor"

    def test_defensive_attribution(self) -> None:
        detector = _make_detector()
        result = detector.suggest_intervention({
            "primary_driver": "defensive_attribution",
            "risk_level": "HIGH",
        })
        assert result == "deescalate"

    def test_linguistic_withdrawal_high(self) -> None:
        detector = _make_detector()
        result = detector.suggest_intervention({
            "primary_driver": "linguistic_withdrawal",
            "risk_level": "HIGH",
        })
        assert result == "validate"

    def test_narrative_incoherence(self) -> None:
        detector = _make_detector()
        result = detector.suggest_intervention({
            "primary_driver": "narrative_incoherence",
            "risk_level": "MODERATE",
        })
        assert result == "reframe"


class TestAssess:
    @pytest.mark.asyncio
    async def test_assess_returns_expected_keys(self) -> None:
        detector = _make_detector()
        history = [{"agent": "a", "content": "hello"}, {"agent": "b", "content": "hi there"}]
        result = await detector.assess(history)

        expected_keys = {
            "overall_collapse_risk", "risk_level", "signal_breakdown",
            "primary_driver", "turns_until_likely_collapse",
            "intervention_recommended", "intervention_type",
            "coc_estimate", "voc_estimate", "is_post_traumatic_growth",
        }
        assert set(result.keys()) == expected_keys
        assert 0.0 <= result["overall_collapse_risk"] <= 1.0
        assert result["risk_level"] in ("CRITICAL", "HIGH", "MODERATE", "LOW", "STABLE")

    @pytest.mark.asyncio
    async def test_collapse_history_grows(self) -> None:
        detector = _make_detector()
        await detector.assess([{"agent": "a", "content": "test"}])
        await detector.assess([{"agent": "b", "content": "test"}])
        assert len(detector.get_collapse_history()) == 2


class TestComputeCocVoc:
    def test_no_episodes(self) -> None:
        detector = _make_detector()
        shadow_a = _make_shadow("a")
        shadow_b = _make_shadow("b")
        coc, voc = detector.compute_coc_voc(shadow_a, shadow_b, [])
        assert isinstance(coc, float)
        assert isinstance(voc, float)
        assert voc == pytest.approx(0.5)  # baseline when no episodes
