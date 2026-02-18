"""Relational Monte Carlo — parallel simulation orchestrator.

Runs N independent timelines with stochastic crisis injection, then
aggregates results into a ``RelationalProbabilityDistribution``.

Key capabilities:
- Batched parallel execution via ``asyncio.gather`` with concurrency cap
- Pareto-distributed severity sampling with configurable override
- Deep statistical analysis: quartile homeostasis, survival curves, CI
- Rich executive report generation
"""

from __future__ import annotations

import asyncio
import logging
import random
import traceback
from collections import Counter, defaultdict
from statistics import mean, median, stdev
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np
from rich.console import Console
from rich.table import Table

from apriori.core.event_generator import StochasticEventGenerator
from apriori.models.shadow_vector import ShadowVector
from apriori.models.simulation import RelationalProbabilityDistribution, TimelineResult
from apriori.observability import trace_monte_carlo_timeline

logger = logging.getLogger(__name__)


class RelationalMonteCarlo:
    """100-timeline parallel simulation runner.

    Executes multi-agent Monte Carlo trajectory analysis across
    parallel timelines with stochastic crisis injection.

    Parameters
    ----------
    n_timelines:
        Number of independent timelines to simulate.
    max_turns_per_timeline:
        Maximum exchanges per timeline.
    crisis_turn_range:
        (min, max) turn range for uniform crisis injection.
    max_workers:
        Maximum concurrent simulations.
    severity_range:
        (min, max) severity range for Pareto sampling.
    """

    def __init__(
        self,
        llm_client: Any,
        n_timelines: int = 100,
        max_turns_per_timeline: int = 40,
        crisis_turn_range: Tuple[int, int] = (10, 25),
        max_workers: int = 10,
        severity_range: Tuple[float, float] = (0.05, 0.95),
    ) -> None:
        self._llm = llm_client
        self._n_timelines = n_timelines
        self._max_turns = max_turns_per_timeline
        self._crisis_turn_range = crisis_turn_range
        self._max_workers = max_workers
        self._severity_range = severity_range
        self._event_generator = StochasticEventGenerator(llm_client)

    def __repr__(self) -> str:
        return (
            f"RelationalMonteCarlo(n={self._n_timelines}, "
            f"max_turns={self._max_turns}, "
            f"workers={self._max_workers})"
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def run_ensemble(
        self,
        shadow_a: ShadowVector,
        shadow_b: ShadowVector,
        pair_id: str,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> RelationalProbabilityDistribution:
        """Execute full Monte Carlo ensemble across all timelines.

        Parameters
        ----------
        shadow_a, shadow_b:
            Agent shadow vectors.
        pair_id:
            Unique pair identifier.
        progress_callback:
            Optional ``fn(completed, total)`` called after each batch.

        Returns
        -------
        RelationalProbabilityDistribution
            Aggregate distribution over all timelines.
        """
        param_sets = self._generate_parameter_sets()
        semaphore = asyncio.Semaphore(self._max_workers)
        results: List[TimelineResult] = []
        completed = 0

        async def _run_with_sem(params: Dict[str, Any]) -> TimelineResult:
            async with semaphore:
                return await self._run_single_timeline(
                    shadow_a=shadow_a,
                    shadow_b=shadow_b,
                    pair_id=pair_id,
                    seed=params["seed"],
                    crisis_at_turn=params["crisis_at_turn"],
                    severity_override=params["severity"],
                )

        # Run in batches for progress reporting
        batch_size = self._max_workers
        for batch_start in range(0, len(param_sets), batch_size):
            batch = param_sets[batch_start : batch_start + batch_size]
            tasks = [_run_with_sem(p) for p in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for r in batch_results:
                if isinstance(r, Exception):
                    logger.error("Timeline failed: %s", r)
                    # Create a failed placeholder
                    results.append(self._make_failed_timeline(pair_id, batch[0]["seed"]))
                else:
                    results.append(r)

            completed += len(batch)
            if progress_callback:
                progress_callback(min(completed, self._n_timelines), self._n_timelines)

        return RelationalProbabilityDistribution(
            pair_id=pair_id,
            n_simulations=self._n_timelines,
            timelines=results,
        )

    @trace_monte_carlo_timeline
    async def _run_single_timeline(
        self,
        shadow_a: ShadowVector,
        shadow_b: ShadowVector,
        pair_id: str,
        seed: int,
        crisis_at_turn: int = 15,
        severity_override: Optional[float] = None,
    ) -> TimelineResult:
        """Run a single simulated timeline with a given random seed.

        Creates fresh component instances to ensure no state leaks
        between timelines.
        """
        try:
            from apriori.agents.dialogue_graph import run_simulation

            event_gen = StochasticEventGenerator(self._llm)

            result = await run_simulation(
                shadow_a=shadow_a,
                shadow_b=shadow_b,
                llm_client=self._llm,
                event_generator=event_gen,
                max_turns=self._max_turns,
                crisis_at_turn=crisis_at_turn,
                seed=seed,
            )
            return result

        except Exception as exc:
            logger.error(
                "Timeline seed=%d failed: %s\n%s",
                seed, exc, traceback.format_exc(),
            )
            return self._make_failed_timeline(pair_id, seed)

    def analyze_distribution(
        self, dist: RelationalProbabilityDistribution
    ) -> Dict[str, Any]:
        """Deep statistical analysis of the Monte Carlo distribution.

        Returns a dict with:
        - homeostasis_by_severity_quartile: dict of quartile → rate
        - survival_curve: list of (severity_threshold, homeostasis_rate)
        - confidence_intervals: dict of metric → (lower, upper) 95% CI
        - risk_scenarios: top 3 riskiest axis-severity combos
        - recommendation: human-readable verdict
        """
        timelines = dist.timelines
        if not timelines:
            return {"error": "No timelines to analyze"}

        # --- Homeostasis by severity quartile ---
        sorted_by_sev = sorted(timelines, key=lambda t: t.crisis_severity)
        quartile_size = max(1, len(sorted_by_sev) // 4)
        quartiles = {
            "Q1 (low)": sorted_by_sev[:quartile_size],
            "Q2": sorted_by_sev[quartile_size : 2 * quartile_size],
            "Q3": sorted_by_sev[2 * quartile_size : 3 * quartile_size],
            "Q4 (high)": sorted_by_sev[3 * quartile_size :],
        }
        homeostasis_by_quartile = {
            q: (sum(1 for t in ts if t.reached_homeostasis) / len(ts) if ts else 0.0)
            for q, ts in quartiles.items()
        }

        # --- Survival curve ---
        thresholds = [i / 20 for i in range(1, 20)]  # 0.05 to 0.95
        survival_curve: List[Tuple[float, float]] = []
        for thresh in thresholds:
            above = [t for t in timelines if t.crisis_severity >= thresh]
            if above:
                rate = sum(1 for t in above if t.reached_homeostasis) / len(above)
                survival_curve.append((thresh, rate))

        # --- Confidence intervals (bootstrap-free normal approx) ---
        elasticities = [t.narrative_elasticity for t in timelines]
        resiliences = [t.final_resilience_score for t in timelines]
        n = len(timelines)

        def _ci_95(values: List[float]) -> Tuple[float, float]:
            if len(values) < 2:
                return (values[0] if values else 0.0, values[0] if values else 0.0)
            m = mean(values)
            se = stdev(values) / (len(values) ** 0.5)
            return (max(0.0, m - 1.96 * se), min(1.0, m + 1.96 * se))

        h_rate = dist.homeostasis_rate
        h_se = ((h_rate * (1 - h_rate)) / n) ** 0.5 if n > 0 else 0.0

        confidence_intervals = {
            "homeostasis_rate": (
                max(0.0, h_rate - 1.96 * h_se),
                min(1.0, h_rate + 1.96 * h_se),
            ),
            "narrative_elasticity": _ci_95(elasticities),
            "resilience_score": _ci_95(resiliences),
        }

        # --- Risk scenarios ---
        collapsed = [t for t in timelines if not t.reached_homeostasis]
        axis_severity: Dict[str, List[float]] = defaultdict(list)
        for t in collapsed:
            axis_severity[t.crisis_axis].append(t.crisis_severity)

        risk_scenarios = sorted(
            [
                {
                    "axis": axis,
                    "n_collapses": len(sevs),
                    "mean_severity": mean(sevs),
                    "collapse_rate": len(sevs) / max(1, sum(1 for t in timelines if t.crisis_axis == axis)),
                }
                for axis, sevs in axis_severity.items()
            ],
            key=lambda r: r["collapse_rate"],
            reverse=True,
        )[:3]

        # --- Recommendation ---
        if h_rate >= 0.80:
            recommendation = "HIGH COMPATIBILITY — This pair demonstrates strong relational resilience across crisis scenarios."
        elif h_rate >= 0.60:
            recommendation = "MODERATE COMPATIBILITY — Pair recovers in most scenarios but shows vulnerability under high-severity stress."
        elif h_rate >= 0.40:
            recommendation = "GUARDED — Significant collapse risk. Targeted support recommended for vulnerable axes."
        else:
            recommendation = "LOW COMPATIBILITY — Majority of timelines result in belief collapse. Consider pre-emptive intervention."

        return {
            "homeostasis_by_severity_quartile": homeostasis_by_quartile,
            "survival_curve": survival_curve,
            "confidence_intervals": confidence_intervals,
            "risk_scenarios": risk_scenarios,
            "recommendation": recommendation,
        }

    def generate_executive_report(
        self,
        dist: RelationalProbabilityDistribution,
        analysis: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate a Rich-formatted executive report.

        Includes compatibility verdict, Monte Carlo summary table,
        ASCII sparkline survival curve, top risks, and antifragility score.
        """
        if analysis is None:
            analysis = self.analyze_distribution(dist)

        console = Console(record=True, width=100)

        # --- Header ---
        console.print()
        console.print(
            f"[bold magenta]APRIORI Executive Report — Pair: {dist.pair_id}[/bold magenta]"
        )
        console.print(f"[dim]Simulations: {dist.n_simulations} | Computed: {dist.computed_at:%Y-%m-%d %H:%M}[/dim]")
        console.print()

        # --- Compatibility Verdict ---
        recommendation = analysis.get("recommendation", "N/A")
        console.print(f"[bold yellow]Verdict:[/bold yellow] {recommendation}")
        console.print()

        # --- Monte Carlo Summary Table ---
        table = Table(title="Monte Carlo Distribution Summary", expand=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white", justify="right")

        table.add_row("Homeostasis Rate", f"{dist.homeostasis_rate:.1%}")
        table.add_row("Antifragility Rate", f"{dist.antifragility_rate:.1%}")
        table.add_row("Median Elasticity", f"{dist.median_elasticity:.3f}")
        table.add_row("P20 Homeostasis", f"{dist.p20_homeostasis:.1%}")
        table.add_row("P80 Homeostasis", f"{dist.p80_homeostasis:.1%}")
        table.add_row("Primary Collapse Vector", dist.primary_collapse_vector)

        ci = analysis.get("confidence_intervals", {})
        if "homeostasis_rate" in ci:
            lo, hi = ci["homeostasis_rate"]
            table.add_row("95% CI (Homeostasis)", f"[{lo:.1%}, {hi:.1%}]")

        console.print(table)
        console.print()

        # --- Survival Curve (ASCII sparkline) ---
        survival = analysis.get("survival_curve", [])
        if survival:
            console.print("[bold cyan]Survival Curve (Homeostasis Rate by Severity):[/bold cyan]")
            blocks = " ▁▂▃▄▅▆▇█"
            sparkline = ""
            for _thresh, rate in survival:
                idx = int(rate * (len(blocks) - 1))
                sparkline += blocks[idx]
            console.print(f"  Severity  0.05 {'─' * len(sparkline)} 0.95")
            console.print(f"  H-Rate    {sparkline}")
            console.print()

        # --- Quartile Breakdown ---
        quartiles = analysis.get("homeostasis_by_severity_quartile", {})
        if quartiles:
            qt = Table(title="Homeostasis by Severity Quartile")
            qt.add_column("Quartile", style="cyan")
            qt.add_column("Homeostasis Rate", style="white", justify="right")
            for q, rate in quartiles.items():
                qt.add_row(q, f"{rate:.1%}")
            console.print(qt)
            console.print()

        # --- Top 3 Risk Scenarios ---
        risks = analysis.get("risk_scenarios", [])
        if risks:
            rt = Table(title="Top Risk Scenarios")
            rt.add_column("Axis", style="red")
            rt.add_column("Collapses", style="white", justify="right")
            rt.add_column("Mean Severity", style="white", justify="right")
            rt.add_column("Collapse Rate", style="white", justify="right")
            for r in risks:
                rt.add_row(
                    r["axis"],
                    str(r["n_collapses"]),
                    f"{r['mean_severity']:.2f}",
                    f"{r['collapse_rate']:.1%}",
                )
            console.print(rt)
            console.print()

        # --- Antifragility Score ---
        console.print(
            f"[bold green]Antifragility Score:[/bold green] "
            f"{dist.antifragility_rate:.1%} of timelines emerged stronger post-crisis"
        )
        console.print()

        return console.export_text()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _generate_parameter_sets(self) -> List[Dict[str, Any]]:
        """Generate N parameter sets with Pareto-distributed severities."""
        params: List[Dict[str, Any]] = []
        for i in range(self._n_timelines):
            seed = i + 1
            rng = random.Random(seed)

            # Pareto-distributed severity, clamped to range
            raw = (np.random.pareto(1.5) + 1) / 10
            severity = float(
                np.clip(raw, self._severity_range[0], self._severity_range[1])
            )

            crisis_at_turn = rng.randint(*self._crisis_turn_range)

            params.append({
                "seed": seed,
                "severity": severity,
                "crisis_at_turn": crisis_at_turn,
            })
        return params

    @staticmethod
    def _make_failed_timeline(pair_id: str, seed: int) -> TimelineResult:
        """Create a placeholder TimelineResult for a failed simulation."""
        return TimelineResult(
            seed=seed,
            pair_id=pair_id,
            crisis_severity=0.0,
            crisis_axis="unknown",
            reached_homeostasis=False,
            narrative_elasticity=0.0,
            final_resilience_score=0.0,
            antifragile=False,
            turns_total=0,
            belief_collapse_events=0,
            linguistic_convergence_final=0.0,
            full_transcript=[],
            belief_state_snapshots=[],
        )
