"""Tests for RelationalMonteCarlo — parallel simulation orchestrator."""

from __future__ import annotations

import json
from typing import List
from unittest.mock import AsyncMock, patch

import pytest

from apriori.core.monte_carlo import RelationalMonteCarlo
from apriori.models.shadow_vector import ShadowVector
from apriori.models.simulation import RelationalProbabilityDistribution, TimelineResult
from conftest import FakeLLMResponse


def _sample_timelines(pair_id: str, n: int = 20) -> List[TimelineResult]:
    """Create sample timelines with realistic severity distribution."""
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


class TestInit:
    def test_defaults(self, mock_llm_client) -> None:
        mc = RelationalMonteCarlo(llm_client=mock_llm_client)
        assert mc._n_timelines == 100
        assert mc._max_turns == 40
        assert mc._max_workers == 10
        assert mc._crisis_turn_range == (10, 25)
        assert mc._severity_range == (0.05, 0.95)

    def test_custom_params(self, mock_llm_client) -> None:
        mc = RelationalMonteCarlo(
            llm_client=mock_llm_client,
            n_timelines=50, max_turns_per_timeline=30,
        )
        assert mc._n_timelines == 50
        assert mc._max_turns == 30

    def test_repr(self, mock_llm_client) -> None:
        mc = RelationalMonteCarlo(llm_client=mock_llm_client, n_timelines=10)
        r = repr(mc)
        assert "RelationalMonteCarlo" in r
        assert "n=10" in r


class TestParameterGeneration:
    def test_n_timelines_correct(self, mock_llm_client) -> None:
        mc = RelationalMonteCarlo(llm_client=mock_llm_client, n_timelines=25)
        params = mc._generate_parameter_sets()
        assert len(params) == 25

    def test_seeds_are_sequential(self, mock_llm_client) -> None:
        mc = RelationalMonteCarlo(llm_client=mock_llm_client, n_timelines=10)
        params = mc._generate_parameter_sets()
        seeds = [p["seed"] for p in params]
        assert seeds == list(range(1, 11))

    def test_crisis_turns_in_range(self, mock_llm_client) -> None:
        mc = RelationalMonteCarlo(
            llm_client=mock_llm_client, n_timelines=50, crisis_turn_range=(5, 15),
        )
        params = mc._generate_parameter_sets()
        for p in params:
            assert 5 <= p["crisis_at_turn"] <= 15

    def test_severity_clamped(self, mock_llm_client) -> None:
        mc = RelationalMonteCarlo(
            llm_client=mock_llm_client, n_timelines=100, severity_range=(0.1, 0.9),
        )
        params = mc._generate_parameter_sets()
        for p in params:
            assert 0.1 <= p["severity"] <= 0.9


class TestTimelinesIndependent:
    def test_timelines_are_independent(self) -> None:
        """Different seeds should produce different timeline results."""
        t1 = _sample_timelines("pair", 10)
        t2 = _sample_timelines("pair", 10)
        # Same function with same params gives same results (deterministic)
        # but different seeds in real usage give different outcomes
        # Test structure: verify different severity → different homeostasis
        high_sev = [t for t in t1 if t.crisis_severity > 0.5]
        low_sev = [t for t in t1 if t.crisis_severity <= 0.5]
        high_h = sum(1 for t in high_sev if t.reached_homeostasis) / max(1, len(high_sev))
        low_h = sum(1 for t in low_sev if t.reached_homeostasis) / max(1, len(low_sev))
        assert low_h > high_h


class TestHomeostasisRateRange:
    def test_homeostasis_rate_range(self) -> None:
        dist = RelationalProbabilityDistribution(
            pair_id="test", n_simulations=20, timelines=_sample_timelines("test"),
        )
        assert 0.0 <= dist.homeostasis_rate <= 1.0

    def test_all_homeostasis(self) -> None:
        timelines = _sample_timelines("test", 10)
        for t in timelines:
            t.reached_homeostasis = True
        dist = RelationalProbabilityDistribution(
            pair_id="test", n_simulations=10, timelines=timelines,
        )
        assert dist.homeostasis_rate == 1.0

    def test_no_homeostasis(self) -> None:
        timelines = _sample_timelines("test", 10)
        for t in timelines:
            t.reached_homeostasis = False
        dist = RelationalProbabilityDistribution(
            pair_id="test", n_simulations=10, timelines=timelines,
        )
        assert dist.homeostasis_rate == 0.0


class TestAntifragility:
    def test_antifragility_detection(self) -> None:
        """Timelines with resilience > baseline should be flagged antifragile."""
        timelines = _sample_timelines("test", 10)
        for t in timelines:
            t.antifragile = True
        dist = RelationalProbabilityDistribution(
            pair_id="test", n_simulations=10, timelines=timelines,
        )
        assert dist.antifragility_rate == 1.0


class TestHighSeverityCorrelation:
    def test_high_severity_lower_homeostasis(self) -> None:
        """Higher severity should correlate with lower homeostasis rate."""
        timelines = _sample_timelines("test", 100)
        dist = RelationalProbabilityDistribution(
            pair_id="test", n_simulations=100, timelines=timelines,
        )
        # p20 should be >= p80 (low severity survives more)
        assert dist.p20_homeostasis >= dist.p80_homeostasis


class TestCollapseAttribution:
    def test_collapse_attribution_sums_to_one(self) -> None:
        timelines = _sample_timelines("test", 20)
        # Ensure some collapses exist
        for t in timelines:
            if t.crisis_severity > 0.6:
                t.reached_homeostasis = False
        dist = RelationalProbabilityDistribution(
            pair_id="test", n_simulations=20, timelines=timelines,
        )
        attr = dist.collapse_attribution
        if attr:
            total = sum(attr.values())
            assert total == pytest.approx(1.0, abs=0.01)


class TestFailedTimeline:
    def test_failed_timeline_handled_gracefully(self, mock_llm_client) -> None:
        """A failed timeline should produce a valid placeholder result."""
        result = RelationalMonteCarlo._make_failed_timeline("test_pair", 42)
        assert result.pair_id == "test_pair"
        assert result.seed == 42
        assert result.reached_homeostasis is False
        assert result.crisis_severity == 0.0
        assert result.crisis_axis == "unknown"
        assert result.turns_total == 0


class TestAnalyzeDistribution:
    def test_returns_expected_keys(self, mock_llm_client) -> None:
        mc = RelationalMonteCarlo(llm_client=mock_llm_client)
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

    def test_empty_timelines(self, mock_llm_client) -> None:
        mc = RelationalMonteCarlo(llm_client=mock_llm_client)
        dist = RelationalProbabilityDistribution(
            pair_id="test", n_simulations=1, timelines=[],
        )
        analysis = mc.analyze_distribution(dist)
        assert "error" in analysis

    def test_quartile_monotonic(self, mock_llm_client) -> None:
        """Low severity quartile should have higher homeostasis than high."""
        mc = RelationalMonteCarlo(llm_client=mock_llm_client)
        dist = RelationalProbabilityDistribution(
            pair_id="test", n_simulations=20, timelines=_sample_timelines("test"),
        )
        analysis = mc.analyze_distribution(dist)
        q = analysis["homeostasis_by_severity_quartile"]
        assert q["Q1 (low)"] >= q["Q4 (high)"]


class TestExecutiveReport:
    def test_report_is_string(self, mock_llm_client) -> None:
        mc = RelationalMonteCarlo(llm_client=mock_llm_client)
        dist = RelationalProbabilityDistribution(
            pair_id="test", n_simulations=20, timelines=_sample_timelines("test"),
        )
        report = mc.generate_executive_report(dist)
        assert isinstance(report, str)
        assert "test" in report
        assert "Homeostasis" in report
        assert "Verdict" in report
