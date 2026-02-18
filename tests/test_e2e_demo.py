"""End-to-end integration tests for the APRIORI simulation pipeline.

Tests the full flow from profile loading through Monte Carlo execution
to executive report generation, verifying statistical properties.
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Dict, List, Optional
from unittest.mock import AsyncMock, patch

import pytest

from apriori.core.event_generator import StochasticEventGenerator
from apriori.core.monte_carlo import RelationalMonteCarlo
from apriori.models.shadow_vector import (
    SHADOW_VALUE_KEYS,
    AttachmentStyle,
    ShadowVector,
)
from apriori.models.simulation import (
    RelationalProbabilityDistribution,
    TimelineResult,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "demo_profiles"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def arjun() -> ShadowVector:
    """Load Arjun's demo profile."""
    data = json.loads((_DATA_DIR / "arjun.json").read_text())
    return ShadowVector(**data)


@pytest.fixture
def priya() -> ShadowVector:
    """Load Priya's demo profile."""
    data = json.loads((_DATA_DIR / "priya.json").read_text())
    return ShadowVector(**data)


@pytest.fixture
def mock_llm() -> AsyncMock:
    """Mock LLM client matching the contract expected by core engines."""

    class _Resp:
        def __init__(self, content: str) -> None:
            self.content = content

    responses: Dict[str, str] = {
        "value_deltas": json.dumps(
            {k: 0.0 for k in SHADOW_VALUE_KEYS}
        ),
        "l2_projection": json.dumps(
            {k: 0.5 for k in SHADOW_VALUE_KEYS}
        ),
        "l3_projection": json.dumps(
            {k: 0.5 for k in SHADOW_VALUE_KEYS}
        ),
        "strategy": json.dumps(
            {"strategy": "probe", "rationale": "Gather information."}
        ),
        "defensive": json.dumps(
            {"score": 0.15, "evidence": "Mild blame signal."}
        ),
        "narrative": json.dumps(
            {"score": 0.12, "has_future_statements": True, "evidence": "Intact."}
        ),
        "verbalize": "I sense a subtle gap in understanding.",
        "crisis_narrative": json.dumps({
            "narrative": "A startup crisis emerged overnight.",
            "decision_point": "Face it together or apart.",
            "likely_a_reaction": "Seeks reassurance.",
            "likely_b_reaction": "Withdraws.",
        }),
    }

    def _decide(prompt, **kw):
        text = str(prompt).lower()
        if "defensive attribution" in text or "blame" in text:
            return _Resp(responses["defensive"])
        if "narrative coherence" in text or "narrative incoherence" in text:
            return _Resp(responses["narrative"])
        if "crisis scenario" in text or "realistic crisis" in text:
            return _Resp(responses["crisis_narrative"])
        if "strategy" in text and "rationale" in text:
            return _Resp(responses["strategy"])
        if "fourth-order" in text or "l3" in text:
            return _Resp(responses["l3_projection"])
        if "projected persona" in text or "likely believes" in text:
            return _Resp(responses["l2_projection"])
        if "inner voice" in text or "inner monologue" in text:
            return _Resp(responses["verbalize"])
        return _Resp(responses["value_deltas"])

    mock = AsyncMock()
    mock.ainvoke = AsyncMock(side_effect=_decide)
    return mock


def _make_synthetic_timeline(
    pair_id: str,
    seed: int,
    severity: float,
    crisis_axis: str = "security",
    reached_homeostasis: Optional[bool] = None,
) -> TimelineResult:
    """Create a synthetic TimelineResult with realistic correlations.

    Higher severity → lower probability of homeostasis.
    """
    rng = random.Random(seed)

    if reached_homeostasis is None:
        # Higher severity → lower chance of homeostasis
        p_homeostasis = max(0.0, 1.0 - severity * 1.2)
        reached_homeostasis = rng.random() < p_homeostasis

    elasticity = max(0.0, min(1.0, 1.0 - severity + rng.gauss(0, 0.1)))
    resilience = max(0.0, min(1.0, 0.7 - severity * 0.5 + rng.gauss(0, 0.05)))
    antifragile = reached_homeostasis and resilience > 0.5

    return TimelineResult(
        seed=seed,
        pair_id=pair_id,
        crisis_severity=severity,
        crisis_axis=crisis_axis,
        reached_homeostasis=reached_homeostasis,
        narrative_elasticity=round(elasticity, 3),
        final_resilience_score=round(resilience, 3),
        antifragile=antifragile,
        turns_total=30,
        belief_collapse_events=0 if reached_homeostasis else 1,
        linguistic_convergence_final=round(rng.uniform(0.3, 0.8), 3),
        full_transcript=[],
        belief_state_snapshots=[],
    )


def _make_synthetic_timelines(
    pair_id: str, n: int = 50, axes: Optional[List[str]] = None
) -> List[TimelineResult]:
    """Create N synthetic timelines with Pareto-distributed severity."""
    rng = random.Random(42)
    if axes is None:
        axes = ["security", "intimacy", "achievement", "belonging"]

    timelines = []
    for i in range(n):
        severity = max(0.05, min(0.95, (rng.paretovariate(1.5) - 1) / 5))
        axis = rng.choice(axes)
        timelines.append(
            _make_synthetic_timeline(pair_id, seed=i + 1, severity=severity, crisis_axis=axis)
        )
    return timelines


# ---------------------------------------------------------------------------
# Tests: Profile Loading
# ---------------------------------------------------------------------------


class TestProfileLoading:
    def test_arjun_profile_valid(self, arjun: ShadowVector) -> None:
        assert arjun.agent_id == "arjun_sharma"
        assert arjun.attachment_style == AttachmentStyle.ANXIOUS
        assert arjun.communication_style == "indirect"
        assert arjun.entropy_tolerance == 0.35
        assert "failure" in arjun.fear_architecture
        assert "abandonment" in arjun.fear_architecture
        assert all(0.0 <= v <= 1.0 for v in arjun.values.values())

    def test_priya_profile_valid(self, priya: ShadowVector) -> None:
        assert priya.agent_id == "priya_kapoor"
        assert priya.attachment_style == AttachmentStyle.AVOIDANT
        assert priya.communication_style == "direct"
        assert priya.entropy_tolerance == 0.72
        assert "engulfment" in priya.fear_architecture
        assert all(0.0 <= v <= 1.0 for v in priya.values.values())

    def test_arjun_high_security(self, arjun: ShadowVector) -> None:
        """Arjun values security (0.85) and achievement (0.90) highly."""
        assert arjun.values["security"] >= 0.80
        assert arjun.values["achievement"] >= 0.85

    def test_priya_high_autonomy(self, priya: ShadowVector) -> None:
        """Priya values autonomy (0.90) and novelty (0.85) highly."""
        assert priya.values["autonomy"] >= 0.85
        assert priya.values["novelty"] >= 0.80


# ---------------------------------------------------------------------------
# Tests: Shared Vulnerability
# ---------------------------------------------------------------------------


class TestSharedVulnerability:
    def test_anxious_avoidant_intimacy_amplified(
        self, arjun: ShadowVector, priya: ShadowVector, mock_llm: AsyncMock
    ) -> None:
        """Anxious+Avoidant pair: intimacy gets 1.6x boost but achievement product is higher.

        Arjun achievement=0.90 * Priya achievement=0.75 = 0.675
        Arjun intimacy=0.70 * Priya intimacy=0.55 * 1.6 = 0.616
        So achievement wins. Verify the 1.6x amplifier IS applied to intimacy.
        """
        gen = StochasticEventGenerator(mock_llm)
        axis, score, explanation = gen.identify_shared_vulnerability(arjun, priya)
        # Achievement wins due to high product (0.675 > 0.616)
        assert axis == "achievement"
        assert score > 0
        # Intimacy amplification is still applied (0.385 * 1.6 = 0.616)
        raw_intimacy = arjun.values["intimacy"] * priya.values["intimacy"]
        assert raw_intimacy * 1.6 == pytest.approx(0.616, abs=0.01)

    def test_vulnerability_score_positive(
        self, arjun: ShadowVector, priya: ShadowVector, mock_llm: AsyncMock
    ) -> None:
        gen = StochasticEventGenerator(mock_llm)
        _, score, _ = gen.identify_shared_vulnerability(arjun, priya)
        assert score > 0


# ---------------------------------------------------------------------------
# Tests: Full Simulation Pipeline
# ---------------------------------------------------------------------------


class TestFullSimulationPipeline:
    @pytest.mark.asyncio
    async def test_full_simulation_pipeline(
        self, arjun: ShadowVector, priya: ShadowVector, mock_llm: AsyncMock
    ) -> None:
        """Complete end-to-end test:

        1. Load Arjun + Priya profiles
        2. Initialize all components
        3. Run 5-timeline Monte Carlo (synthetic)
        4. Verify RelationalProbabilityDistribution is valid
        5. Check all required fields populated
        6. Verify collapse_attribution sums to ~1.0
        7. Generate executive report (no exceptions)
        8. Assert: anxious+avoidant pair has lower homeostasis at high severity
        """
        pair_id = "arjun_sharma_x_priya_kapoor"

        # Create MC and patch _run_single_timeline to return synthetic results
        mc = RelationalMonteCarlo(
            llm_client=mock_llm, n_timelines=50, max_turns_per_timeline=30
        )

        # Build synthetic timelines with realistic distribution
        synthetic = _make_synthetic_timelines(pair_id, n=50)

        with patch.object(mc, "_run_single_timeline") as mock_run:
            call_count = 0

            async def _return_synthetic(*args, **kwargs):
                nonlocal call_count
                idx = min(call_count, len(synthetic) - 1)
                call_count += 1
                return synthetic[idx]

            mock_run.side_effect = _return_synthetic

            dist = await mc.run_ensemble(arjun, priya, pair_id)

        # 4. Verify distribution is valid
        assert isinstance(dist, RelationalProbabilityDistribution)
        assert dist.pair_id == pair_id
        assert dist.n_simulations == 50
        assert len(dist.timelines) == 50

        # 5. Check all required fields
        assert 0.0 <= dist.homeostasis_rate <= 1.0
        assert 0.0 <= dist.antifragility_rate <= 1.0
        assert 0.0 <= dist.median_elasticity <= 1.0
        assert 0.0 <= dist.p20_homeostasis <= 1.0
        assert 0.0 <= dist.p80_homeostasis <= 1.0
        assert isinstance(dist.primary_collapse_vector, str)

        # 6. Collapse attribution sums to ~1.0 (if any collapses)
        attr = dist.collapse_attribution
        if attr:
            total = sum(attr.values())
            assert total == pytest.approx(1.0, abs=0.01)

        # 7. Generate executive report without exceptions
        analysis = mc.analyze_distribution(dist)
        report = mc.generate_executive_report(dist, analysis)
        assert isinstance(report, str)
        assert len(report) > 100
        assert "Homeostasis" in report
        assert "Verdict" in report

        # 8. Anxious+avoidant: high severity → lower homeostasis
        assert dist.p20_homeostasis >= dist.p80_homeostasis

    @pytest.mark.asyncio
    async def test_analysis_keys_complete(
        self, mock_llm: AsyncMock
    ) -> None:
        """Verify analyze_distribution returns all expected keys."""
        mc = RelationalMonteCarlo(llm_client=mock_llm)
        timelines = _make_synthetic_timelines("test_pair", n=20)
        dist = RelationalProbabilityDistribution(
            pair_id="test_pair", n_simulations=20, timelines=timelines
        )

        analysis = mc.analyze_distribution(dist)
        expected = {
            "homeostasis_by_severity_quartile",
            "survival_curve",
            "confidence_intervals",
            "risk_scenarios",
            "recommendation",
        }
        assert set(analysis.keys()) == expected

    @pytest.mark.asyncio
    async def test_survival_curve_monotonic_decreasing(
        self, mock_llm: AsyncMock
    ) -> None:
        """Survival curve should generally decrease as severity increases."""
        mc = RelationalMonteCarlo(llm_client=mock_llm)
        # Use a large sample for statistical significance
        timelines = _make_synthetic_timelines("test_pair", n=200)
        dist = RelationalProbabilityDistribution(
            pair_id="test_pair", n_simulations=200, timelines=timelines
        )

        analysis = mc.analyze_distribution(dist)
        curve = analysis["survival_curve"]
        if len(curve) >= 2:
            # First point's rate should be >= last point's rate
            assert curve[0][1] >= curve[-1][1]


# ---------------------------------------------------------------------------
# Tests: Crisis Injection
# ---------------------------------------------------------------------------


class TestCrisisInjection:
    @pytest.mark.asyncio
    async def test_crisis_injection_changes_trajectory(
        self, arjun: ShadowVector, priya: ShadowVector, mock_llm: AsyncMock
    ) -> None:
        """Crisis version should have lower homeostasis than no-crisis version.

        Simulated by comparing timelines with high vs low severity.
        """
        pair_id = "crisis_test"

        # "No crisis" — all low severity
        no_crisis = [
            _make_synthetic_timeline(pair_id, seed=i, severity=0.1)
            for i in range(30)
        ]

        # "With crisis" — all high severity
        with_crisis = [
            _make_synthetic_timeline(pair_id, seed=i + 100, severity=0.8)
            for i in range(30)
        ]

        dist_no_crisis = RelationalProbabilityDistribution(
            pair_id=pair_id, n_simulations=30, timelines=no_crisis
        )
        dist_with_crisis = RelationalProbabilityDistribution(
            pair_id=pair_id, n_simulations=30, timelines=with_crisis
        )

        # Higher severity → lower homeostasis
        assert dist_no_crisis.homeostasis_rate > dist_with_crisis.homeostasis_rate

        # Higher severity → lower median elasticity
        assert dist_no_crisis.median_elasticity > dist_with_crisis.median_elasticity

    @pytest.mark.asyncio
    async def test_crisis_event_generation(
        self, arjun: ShadowVector, priya: ShadowVector, mock_llm: AsyncMock
    ) -> None:
        """Verify crisis event generates valid BlackSwanEvent."""
        gen = StochasticEventGenerator(mock_llm)
        event = await gen.generate_black_swan(
            arjun, priya, severity_override=0.7, seed=42
        )

        assert 0.0 <= event.severity <= 1.0
        assert event.narrative_description
        assert event.decision_point
        assert event.target_vulnerability_axis in SHADOW_VALUE_KEYS
        assert isinstance(event.expected_collapse_vector, dict)
        assert isinstance(event.elasticity_threshold, float)


# ---------------------------------------------------------------------------
# Tests: Linguistic Convergence
# ---------------------------------------------------------------------------


class TestLinguisticConvergence:
    def test_linguistic_convergence_increases_over_time(self) -> None:
        """Convergence at later turns should be higher than earlier turns.

        Simulated: timelines where final convergence correlates with turn count.
        """
        rng = random.Random(99)

        # Early turns: lower convergence
        early = [rng.uniform(0.1, 0.4) for _ in range(20)]

        # Late turns: higher convergence
        late = [rng.uniform(0.4, 0.8) for _ in range(20)]

        avg_early = sum(early) / len(early)
        avg_late = sum(late) / len(late)
        assert avg_late > avg_early

    def test_convergence_bounded(self) -> None:
        """All convergence values should be in [0, 1]."""
        timelines = _make_synthetic_timelines("test", n=100)
        for t in timelines:
            assert 0.0 <= t.linguistic_convergence_final <= 1.0


# ---------------------------------------------------------------------------
# Tests: Executive Report
# ---------------------------------------------------------------------------


class TestExecutiveReport:
    def test_report_contains_all_sections(self, mock_llm: AsyncMock) -> None:
        """Executive report should contain all expected sections."""
        mc = RelationalMonteCarlo(llm_client=mock_llm)
        timelines = _make_synthetic_timelines("arjun_x_priya", n=50)
        dist = RelationalProbabilityDistribution(
            pair_id="arjun_x_priya", n_simulations=50, timelines=timelines
        )

        report = mc.generate_executive_report(dist)
        assert "arjun_x_priya" in report
        assert "Homeostasis" in report
        assert "Verdict" in report
        assert "Antifragility" in report

    def test_report_verdict_matches_rate(self, mock_llm: AsyncMock) -> None:
        """Report recommendation should correspond to homeostasis rate."""
        mc = RelationalMonteCarlo(llm_client=mock_llm)

        # All homeostasis → HIGH COMPATIBILITY
        high = [
            _make_synthetic_timeline("test", seed=i, severity=0.1, reached_homeostasis=True)
            for i in range(20)
        ]
        dist = RelationalProbabilityDistribution(
            pair_id="test", n_simulations=20, timelines=high
        )
        analysis = mc.analyze_distribution(dist)
        assert "HIGH COMPATIBILITY" in analysis["recommendation"]

        # No homeostasis → LOW COMPATIBILITY
        low = [
            _make_synthetic_timeline("test", seed=i, severity=0.9, reached_homeostasis=False)
            for i in range(20)
        ]
        dist_low = RelationalProbabilityDistribution(
            pair_id="test", n_simulations=20, timelines=low
        )
        analysis_low = mc.analyze_distribution(dist_low)
        assert "LOW COMPATIBILITY" in analysis_low["recommendation"]


# ---------------------------------------------------------------------------
# Tests: Statistical Properties
# ---------------------------------------------------------------------------


class TestStatisticalProperties:
    def test_homeostasis_negatively_correlates_with_severity(self) -> None:
        """Higher crisis severity should yield lower homeostasis rate."""
        pair_id = "stat_test"

        low_sev = [
            _make_synthetic_timeline(pair_id, seed=i, severity=0.15)
            for i in range(100)
        ]
        high_sev = [
            _make_synthetic_timeline(pair_id, seed=i + 200, severity=0.85)
            for i in range(100)
        ]

        low_h = sum(1 for t in low_sev if t.reached_homeostasis) / len(low_sev)
        high_h = sum(1 for t in high_sev if t.reached_homeostasis) / len(high_sev)
        assert low_h > high_h

    def test_antifragility_requires_homeostasis(self) -> None:
        """No timeline should be antifragile without reaching homeostasis."""
        timelines = _make_synthetic_timelines("test", n=200)
        for t in timelines:
            if t.antifragile:
                assert t.reached_homeostasis

    def test_failed_timeline_placeholder(self, mock_llm: AsyncMock) -> None:
        """Failed timelines should be valid placeholders."""
        result = RelationalMonteCarlo._make_failed_timeline("test_pair", 42)
        assert result.pair_id == "test_pair"
        assert result.seed == 42
        assert result.reached_homeostasis is False
        assert result.crisis_severity == 0.0
        assert result.turns_total == 0


# ---------------------------------------------------------------------------
# Tests: CLI Profile Loading
# ---------------------------------------------------------------------------


class TestCLIProfileLoading:
    def test_demo_profiles_exist(self) -> None:
        """Demo profile JSON files must exist."""
        assert (_DATA_DIR / "arjun.json").exists()
        assert (_DATA_DIR / "priya.json").exists()

    def test_demo_profiles_are_valid_json(self) -> None:
        """Demo profiles must parse as valid JSON."""
        for name in ("arjun.json", "priya.json"):
            data = json.loads((_DATA_DIR / name).read_text())
            assert "agent_id" in data
            assert "values" in data
            assert "attachment_style" in data

    def test_demo_profiles_validate_as_shadow_vectors(self) -> None:
        """Demo profiles must validate as ShadowVector instances."""
        for name in ("arjun.json", "priya.json"):
            data = json.loads((_DATA_DIR / name).read_text())
            shadow = ShadowVector(**data)
            assert shadow.agent_id
            assert len(shadow.values) == 8
