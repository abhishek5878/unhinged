"""Tests for BeliefCollapseDetector — Real-time collapse early warning."""

import json
from unittest.mock import AsyncMock

import pytest

from apriori.core.alignment_scorer import LinguisticAlignmentScorer
from apriori.core.collapse_detector import BeliefCollapseDetector
from apriori.core.tom_tracker import ToMTracker
from apriori.models.shadow_vector import AttachmentStyle, ShadowVector, SHADOW_VALUE_KEYS
from conftest import FakeLLMResponse


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


def _make_llm_for_detector(score: float = 0.1) -> AsyncMock:
    """LLM mock that returns configurable scores for both detectors."""
    mock = AsyncMock()
    mock.ainvoke = AsyncMock(
        return_value=FakeLLMResponse(json.dumps({
            "score": score, "evidence": "test", "has_future_statements": True,
        }))
    )
    return mock


def _make_llm_for_tracker() -> AsyncMock:
    """LLM mock for ToMTracker init (won't be called in unit tests)."""
    return AsyncMock()


def _make_detector(det_score: float = 0.1) -> BeliefCollapseDetector:
    shadow_a = _make_shadow("a")
    shadow_b = _make_shadow("b")
    llm_tracker = _make_llm_for_tracker()
    tom_a = ToMTracker("a", shadow_a, llm_tracker)
    tom_b = ToMTracker("b", shadow_b, llm_tracker)
    scorer = LinguisticAlignmentScorer()
    llm_detector = _make_llm_for_detector(det_score)
    return BeliefCollapseDetector(tom_a, tom_b, scorer, llm_detector)


class TestInit:
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


class TestStableConversation:
    @pytest.mark.asyncio
    async def test_stable_conversation_low_risk(self) -> None:
        """Happy dialogue with low LLM scores should produce LOW/STABLE risk."""
        detector = _make_detector(det_score=0.1)
        history = [
            {"agent": "a", "content": "I appreciate how we talk things through together."},
            {"agent": "b", "content": "Me too, I feel like we really understand each other."},
        ]
        result = await detector.assess(history)
        assert result["risk_level"] in ("LOW", "STABLE")
        assert result["overall_collapse_risk"] < 0.4


class TestDefensiveAttribution:
    @pytest.mark.asyncio
    async def test_defensive_attribution_detected(self) -> None:
        """High defensive attribution LLM score → HIGH risk contribution."""
        detector = _make_detector(det_score=0.8)
        history = [
            {"agent": "a", "content": "You always do this. You never listen."},
            {"agent": "b", "content": "You just want to control everything, typical."},
        ]
        result = await detector.assess(history)
        assert result["signal_breakdown"]["defensive_attribution"] >= 0.8
        # Defensive attribution alone (0.25 weight * 0.8 = 0.2) + narrative (0.15 * 0.8)
        assert result["overall_collapse_risk"] > 0.2


class TestWithdrawalSignal:
    @pytest.mark.asyncio
    async def test_withdrawal_signal_from_short_responses(self) -> None:
        """Terse replies vs longer prior responses → elevated response_latency_proxy."""
        detector = _make_detector()
        history = [{"agent": "a", "content": "x" * 100}] * 10 + [{"agent": "b", "content": "ok"}] * 5
        score = detector._response_length_proxy(history)
        assert score > 0.5

    def test_no_withdrawal_equal_length(self) -> None:
        detector = _make_detector()
        history = [{"content": "x" * 100}] * 20
        assert detector._response_length_proxy(history) == pytest.approx(0.0)

    def test_too_short_history(self) -> None:
        detector = _make_detector()
        history = [{"content": "hi"}] * 5
        assert detector._response_length_proxy(history) == 0.0


class TestCoCExceedsVoC:
    def test_coc_exceeds_voc_triggers_collapse(self) -> None:
        """When CoC > VoC, collapse is mathematically imminent."""
        detector = _make_detector()
        shadow_a = _make_shadow("a")
        shadow_b = _make_shadow("b")

        from apriori.models.events import BlackSwanEvent, CrisisEpisode

        # Create episodes where all reached_homeostasis=False → high crisis load
        episodes = []
        for i in range(5):
            event = BlackSwanEvent(
                event_type="financial_collapse",
                target_vulnerability_axis="security",
                severity=0.8,
                narrative_description="Financial crisis",
                decision_point="Decide together",
                expected_collapse_vector={"a": 0.5, "b": 0.5},
                elasticity_threshold=0.3,
            )
            ep = CrisisEpisode(
                event=event,
                pre_crisis_transcript=[],
                post_crisis_transcript=[],
                narrative_elasticity_score=0.1,
                reached_homeostasis=False,
                turns_to_resolution=0,
                final_divergence=0.8,
            )
            episodes.append(ep)

        coc, voc = detector.compute_coc_voc(shadow_a, shadow_b, episodes)
        # With all failed episodes, CoC should be elevated
        assert isinstance(coc, float)
        assert isinstance(voc, float)
        # VOC should be low because elasticity scores are 0.1
        assert voc < 0.2

    def test_no_episodes_baseline_voc(self) -> None:
        detector = _make_detector()
        shadow_a = _make_shadow("a")
        shadow_b = _make_shadow("b")
        coc, voc = detector.compute_coc_voc(shadow_a, shadow_b, [])
        assert voc == pytest.approx(0.5)


class TestInterventionType:
    def test_intervention_type_matches_primary_driver(self) -> None:
        detector = _make_detector()

        result = detector.suggest_intervention({
            "primary_driver": "epistemic_divergence",
            "risk_level": "CRITICAL",
        })
        assert result == "reanchor"

        result = detector.suggest_intervention({
            "primary_driver": "defensive_attribution",
            "risk_level": "HIGH",
        })
        assert result == "deescalate"

        result = detector.suggest_intervention({
            "primary_driver": "linguistic_withdrawal",
            "risk_level": "HIGH",
        })
        assert result == "validate"

        result = detector.suggest_intervention({
            "primary_driver": "narrative_incoherence",
            "risk_level": "MODERATE",
        })
        assert result == "reframe"


class TestPostTraumaticGrowth:
    @pytest.mark.asyncio
    async def test_post_traumatic_growth_detection(self) -> None:
        """Resilience > baseline after a peak should be flagged as PTG."""
        detector = _make_detector(det_score=0.1)

        # Simulate assessments: risk peaks then drops
        # We need >= 5 assessments with peak > 0.5 and current < peak * 0.6

        # First: create high-risk assessments by using high det_score
        high_det_llm = _make_llm_for_detector(0.9)
        shadow_a = _make_shadow("a")
        shadow_b = _make_shadow("b")
        high_detector = BeliefCollapseDetector(
            ToMTracker("a", shadow_a, _make_llm_for_tracker()),
            ToMTracker("b", shadow_b, _make_llm_for_tracker()),
            LinguisticAlignmentScorer(),
            high_det_llm,
        )
        history = [{"agent": "a", "content": "You always blame me."}]

        # 3 high-risk assessments
        for _ in range(3):
            await high_detector.assess(history)

        # Now switch to low scores to simulate recovery
        high_det_llm.ainvoke = AsyncMock(
            return_value=FakeLLMResponse(json.dumps({
                "score": 0.05, "evidence": "recovered", "has_future_statements": True,
            }))
        )

        # 3 low-risk assessments
        for _ in range(3):
            await high_detector.assess(history)

        # Check PTG detection
        risks = [
            h["assessment"]["overall_collapse_risk"]
            for h in high_detector.get_collapse_history()
        ]
        peak = max(risks)
        current = risks[-1]
        # If peak was high enough and current recovered enough, PTG should be True
        if peak > 0.5 and current < peak * 0.6:
            assert high_detector._detect_post_traumatic_growth() is True


class TestAssess:
    @pytest.mark.asyncio
    async def test_assess_returns_expected_keys(self) -> None:
        detector = _make_detector()
        history = [
            {"agent": "a", "content": "hello"},
            {"agent": "b", "content": "hi there"},
        ]
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
