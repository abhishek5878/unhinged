from __future__ import annotations

from collections import Counter
from datetime import datetime
from statistics import median
from typing import Dict, List
from uuid import uuid4

from pydantic import BaseModel, Field, computed_field
from rich.console import Console
from rich.table import Table


class TimelineResult(BaseModel):
    """Result of a single Monte Carlo simulated timeline."""

    timeline_id: str = Field(default_factory=lambda: str(uuid4()))
    seed: int
    pair_id: str
    crisis_severity: float = Field(..., ge=0.0, le=1.0)
    crisis_axis: str
    reached_homeostasis: bool
    narrative_elasticity: float = Field(..., ge=0.0, le=1.0)
    final_resilience_score: float = Field(..., ge=0.0, le=1.0)
    antifragile: bool = Field(
        ..., description="True if resilience > baseline after crisis"
    )
    turns_total: int = Field(..., ge=0)
    belief_collapse_events: int = Field(..., ge=0)
    linguistic_convergence_final: float = Field(..., ge=0.0, le=1.0)
    full_transcript: List[Dict] = Field(default_factory=list)
    belief_state_snapshots: List[Dict] = Field(
        default_factory=list, description="Snapshot every 5 turns"
    )

    def __repr__(self) -> str:
        status = "H" if self.reached_homeostasis else "C"
        af = "+AF" if self.antifragile else ""
        return (
            f"Timeline({self.timeline_id[:8]}… [{status}{af}] "
            f"sev={self.crisis_severity:.2f} "
            f"elas={self.narrative_elasticity:.2f} "
            f"turns={self.turns_total})"
        )


class RelationalProbabilityDistribution(BaseModel):
    """Aggregate distribution over all Monte Carlo timelines for a pair."""

    pair_id: str
    n_simulations: int = Field(..., ge=1)
    timelines: List[TimelineResult]
    computed_at: datetime = Field(default_factory=datetime.utcnow)

    @computed_field  # type: ignore[misc]
    @property
    def homeostasis_rate(self) -> float:
        """Fraction of timelines that reached homeostasis."""
        if not self.timelines:
            return 0.0
        return sum(1 for t in self.timelines if t.reached_homeostasis) / len(self.timelines)

    @computed_field  # type: ignore[misc]
    @property
    def antifragility_rate(self) -> float:
        """Fraction of timelines where pair emerged stronger than baseline."""
        if not self.timelines:
            return 0.0
        return sum(1 for t in self.timelines if t.antifragile) / len(self.timelines)

    @computed_field  # type: ignore[misc]
    @property
    def median_elasticity(self) -> float:
        """Median narrative elasticity across all timelines."""
        if not self.timelines:
            return 0.0
        return median(t.narrative_elasticity for t in self.timelines)

    @computed_field  # type: ignore[misc]
    @property
    def collapse_attribution(self) -> Dict[str, float]:
        """Fraction of collapse events attributed to each crisis axis."""
        collapsed = [t for t in self.timelines if not t.reached_homeostasis]
        if not collapsed:
            return {}
        counts: Counter[str] = Counter(t.crisis_axis for t in collapsed)
        total = len(collapsed)
        return {axis: count / total for axis, count in counts.most_common()}

    @computed_field  # type: ignore[misc]
    @property
    def p20_homeostasis(self) -> float:
        """Homeostasis rate when crisis severity > 20th percentile."""
        if not self.timelines:
            return 0.0
        severities = sorted(t.crisis_severity for t in self.timelines)
        threshold = severities[len(severities) // 5] if len(severities) >= 5 else 0.0
        above = [t for t in self.timelines if t.crisis_severity > threshold]
        if not above:
            return 0.0
        return sum(1 for t in above if t.reached_homeostasis) / len(above)

    @computed_field  # type: ignore[misc]
    @property
    def p80_homeostasis(self) -> float:
        """Homeostasis rate when crisis severity > 80th percentile."""
        if not self.timelines:
            return 0.0
        severities = sorted(t.crisis_severity for t in self.timelines)
        idx = int(len(severities) * 0.8)
        threshold = severities[idx] if idx < len(severities) else severities[-1]
        above = [t for t in self.timelines if t.crisis_severity > threshold]
        if not above:
            return 0.0
        return sum(1 for t in above if t.reached_homeostasis) / len(above)

    @computed_field  # type: ignore[misc]
    @property
    def primary_collapse_vector(self) -> str:
        """The crisis axis most frequently causing collapse."""
        attr = self.collapse_attribution
        if not attr:
            return "none"
        return max(attr, key=attr.get)  # type: ignore[arg-type]

    def summary(self) -> str:
        """Return a rich-formatted summary string."""
        console = Console(record=True, width=80)

        table = Table(title=f"APRIORI — Relational Probability Distribution [{self.pair_id}]")
        table.add_column("Metric", style="bold cyan")
        table.add_column("Value", style="bold white")

        table.add_row("Simulations", str(self.n_simulations))
        table.add_row("Homeostasis Rate", f"{self.homeostasis_rate:.1%}")
        table.add_row("Antifragility Rate", f"{self.antifragility_rate:.1%}")
        table.add_row("Median Elasticity", f"{self.median_elasticity:.3f}")
        table.add_row("P20 Homeostasis", f"{self.p20_homeostasis:.1%}")
        table.add_row("P80 Homeostasis", f"{self.p80_homeostasis:.1%}")
        table.add_row("Primary Collapse Vector", self.primary_collapse_vector)

        if self.collapse_attribution:
            attr_str = ", ".join(
                f"{axis}: {pct:.1%}" for axis, pct in self.collapse_attribution.items()
            )
            table.add_row("Collapse Attribution", attr_str)

        console.print(table)
        return console.export_text()

    def __repr__(self) -> str:
        return (
            f"RPD(pair={self.pair_id!r}, n={self.n_simulations}, "
            f"H={self.homeostasis_rate:.1%}, "
            f"AF={self.antifragility_rate:.1%}, "
            f"elas={self.median_elasticity:.3f})"
        )
