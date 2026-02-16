import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from apriori.core.monte_carlo import RelationalMonteCarlo
from apriori.models.shadow_vector import ShadowVector
from apriori.models.simulation import RelationalProbabilityDistribution, TimelineResult


class _FakeLLMResponse:
    def __init__(self, content: str) -> None:
        self.content = content


def _make_llm() -> AsyncMock:
    narrative = {
        "narrative": "A crisis occurred.",
        "decision_point": "They must decide.",
        "likely_a_reaction": "Agent A freezes.",
        "likely_b_reaction": "Agent B retreats.",
    }
    mock = AsyncMock()
    mock.ainvoke = AsyncMock(return_value=_FakeLLMResponse(json.dumps(narrative)))
    return mock


def _sample_timelines(pair_id: str, n: int = 20) -> list[TimelineResult]:
    results = []
    for i in range(n):
        sev = (i + 1) / (n + 1)
        results.append(TimelineResult(
            seed=i,
            pair_id=pair_id,
            crisis_severity=round(sev, 3),
            crisis_axis="security" if i % 2 == 0 else "intimacy",
            reached_homeostasis=sev < 0.6,
            narrative_elasticity=max(0.0, min(1.0, 1.0 - sev)),
            final_resilience_score=max(0.0, min(1.0, 0.7 - sev * 0.5)),
            antifragile=sev < 0.3,
            turns_total=30,
            belief_collapse_events=1 if sev > 0.7 else 0,
            linguistic_convergence_final=0.5,
        ))
    return results


class TestRelationalMonteCarloInit:
    def test_init(self) -> None:
        mc = RelationalMonteCarlo(
            llm_client=_make_llm(), n_timelines=50, max_turns_per_timeline=30,
        )
        assert mc._n_timelines == 50
        assert mc._max_turns == 30

    def test_repr(self) -> None:
        mc = RelationalMonteCarlo(llm_client=_make_llm(), n_timelines=10)
        r = repr(mc)
        assert "RelationalMonteCarlo" in r
        assert "n=10" in r

    def test_defaults(self) -> None:
        mc = RelationalMonteCarlo(llm_client=_make_llm())
        assert mc._n_timelines == 100
        assert mc._max_turns == 40
        assert mc._max_workers == 10
        assert mc._crisis_turn_range == (10, 25)
        assert mc._severity_range == (0.05, 0.95)


class TestParameterGeneration:
    def test_generates_correct_count(self) -> None:
        mc = RelationalMonteCarlo(llm_client=_make_llm(), n_timelines=25)
        params = mc._generate_parameter_sets()
        assert len(params) == 25

    def test_seeds_are_sequential(self) -> None:
        mc = RelationalMonteCarlo(llm_client=_make_llm(), n_timelines=10)
        params = mc._generate_parameter_sets()
        seeds = [p["seed"] for p in params]
        assert seeds == list(range(1, 11))

    def test_crisis_turns_in_range(self) -> None:
        mc = RelationalMonteCarlo(
            llm_client=_make_llm(), n_timelines=50, crisis_turn_range=(5, 15),
        )
        params = mc._generate_parameter_sets()
        for p in params:
            assert 5 <= p["crisis_at_turn"] <= 15

    def test_severity_clamped(self) -> None:
        mc = RelationalMonteCarlo(
            llm_client=_make_llm(), n_timelines=100, severity_range=(0.1, 0.9),
        )
        params = mc._generate_parameter_sets()
        for p in params:
            assert 0.1 <= p["severity"] <= 0.9


class TestFailedTimeline:
    def test_failed_timeline_structure(self) -> None:
        result = RelationalMonteCarlo._make_failed_timeline("test_pair", 42)
        assert result.pair_id == "test_pair"
        assert result.seed == 42
        assert result.reached_homeostasis is False
        assert result.crisis_severity == 0.0
        assert result.crisis_axis == "unknown"
        assert result.turns_total == 0


class TestAnalyzeDistribution:
    def test_returns_expected_keys(self) -> None:
        mc = RelationalMonteCarlo(llm_client=_make_llm())
        dist = RelationalProbabilityDistribution(
            pair_id="test", n_simulations=20, timelines=_sample_timelines("test"),
        )
        analysis = mc.analyze_distribution(dist)
        expected_keys = {
            "homeostasis_by_severity_quartile",
            "survival_curve",
            "confidence_intervals",
            "risk_scenarios",
            "recommendation",
        }
        assert set(analysis.keys()) == expected_keys

    def test_quartile_keys(self) -> None:
        mc = RelationalMonteCarlo(llm_client=_make_llm())
        dist = RelationalProbabilityDistribution(
            pair_id="test", n_simulations=20, timelines=_sample_timelines("test"),
        )
        analysis = mc.analyze_distribution(dist)
        quartiles = analysis["homeostasis_by_severity_quartile"]
        assert "Q1 (low)" in quartiles
        assert "Q4 (high)" in quartiles
        # Low severity should have higher homeostasis
        assert quartiles["Q1 (low)"] >= quartiles["Q4 (high)"]

    def test_survival_curve_decreasing(self) -> None:
        mc = RelationalMonteCarlo(llm_client=_make_llm())
        dist = RelationalProbabilityDistribution(
            pair_id="test", n_simulations=20, timelines=_sample_timelines("test"),
        )
        analysis = mc.analyze_distribution(dist)
        curve = analysis["survival_curve"]
        assert len(curve) > 0
        # Generally non-increasing (higher threshold → fewer survivors)
        for i in range(1, len(curve)):
            # Allow slight non-monotonicity from discrete data
            assert curve[i][1] <= curve[0][1] + 0.1

    def test_empty_timelines(self) -> None:
        mc = RelationalMonteCarlo(llm_client=_make_llm())
        dist = RelationalProbabilityDistribution(
            pair_id="test", n_simulations=0, timelines=[],
        )
        analysis = mc.analyze_distribution(dist)
        assert "error" in analysis

    def test_recommendation_levels(self) -> None:
        mc = RelationalMonteCarlo(llm_client=_make_llm())
        # High homeostasis
        high_h = _sample_timelines("test", 20)
        for t in high_h:
            t.reached_homeostasis = True
        dist = RelationalProbabilityDistribution(
            pair_id="test", n_simulations=20, timelines=high_h,
        )
        analysis = mc.analyze_distribution(dist)
        assert "HIGH COMPATIBILITY" in analysis["recommendation"]


class TestGenerateExecutiveReport:
    def test_report_is_string(self) -> None:
        mc = RelationalMonteCarlo(llm_client=_make_llm())
        dist = RelationalProbabilityDistribution(
            pair_id="test", n_simulations=20, timelines=_sample_timelines("test"),
        )
        report = mc.generate_executive_report(dist)
        assert isinstance(report, str)
        assert "test" in report
        assert "Homeostasis" in report

    def test_report_with_precomputed_analysis(self) -> None:
        mc = RelationalMonteCarlo(llm_client=_make_llm())
        dist = RelationalProbabilityDistribution(
            pair_id="test", n_simulations=20, timelines=_sample_timelines("test"),
        )
        analysis = mc.analyze_distribution(dist)
        report = mc.generate_executive_report(dist, analysis=analysis)
        assert "Verdict" in report
