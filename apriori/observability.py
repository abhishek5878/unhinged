"""LangSmith observability — tracing decorators and centralized observer.

Provides three decorators for automatic tracing of core operations:
- ``trace_tom_update``: traces each ``hidden_thought()`` call
- ``trace_crisis_injection``: traces Black Swan event generation
- ``trace_monte_carlo_timeline``: traces individual timeline simulation

Plus ``AprioriObserver`` for structured dataset logging.
"""

from __future__ import annotations

import functools
import logging
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List

from apriori.config import settings

logger = logging.getLogger(__name__)

# Conditional import — graceful degradation when langsmith not available
try:
    from langsmith import Client
    from langsmith.run_helpers import get_current_run_tree, traceable

    _LANGSMITH_AVAILABLE = True
except ImportError:
    _LANGSMITH_AVAILABLE = False
    logger.warning("langsmith not installed; tracing disabled")


# ---------------------------------------------------------------------------
# Tracing decorators
# ---------------------------------------------------------------------------


def trace_tom_update(func: Callable) -> Callable:
    """Decorator: traces each hidden_thought() call with full metadata.

    Tags: tom, belief-update
    Metadata: agent_id, epistemic_divergence, collapse_risk, turn_number
    """
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        result = await func(self, *args, **kwargs)
        if _LANGSMITH_AVAILABLE and settings.langsmith_tracing:
            try:
                run = get_current_run_tree()
                if run:
                    run.add_metadata({
                        "agent_id": self.agent_id,
                        "epistemic_divergence": result.get("epistemic_divergence"),
                        "collapse_risk": result.get("collapse_risk"),
                        "turn_number": len(self._thought_log),
                    })
                    run.tags = list(set((run.tags or []) + ["tom", "belief-update"]))
            except Exception as exc:
                logger.debug("LangSmith trace_tom_update failed: %s", exc)
        return result

    if _LANGSMITH_AVAILABLE:
        wrapper = traceable(name="tom_hidden_thought", tags=["tom", "belief-update"])(wrapper)

    return wrapper


def trace_crisis_injection(func: Callable) -> Callable:
    """Decorator: traces each Black Swan event injection with full parameters.

    Tags: crisis, entropy
    Metadata: target_axis, severity, event_type, elasticity_threshold
    """
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        result = await func(self, *args, **kwargs)
        if _LANGSMITH_AVAILABLE and settings.langsmith_tracing:
            try:
                run = get_current_run_tree()
                if run:
                    run.add_metadata({
                        "target_axis": result.target_vulnerability_axis,
                        "severity": result.severity,
                        "event_type": result.event_type.value if hasattr(result.event_type, "value") else str(result.event_type),
                        "elasticity_threshold": result.elasticity_threshold,
                    })
                    run.tags = list(set((run.tags or []) + ["crisis", "entropy"]))
            except Exception as exc:
                logger.debug("LangSmith trace_crisis_injection failed: %s", exc)
        return result

    if _LANGSMITH_AVAILABLE:
        wrapper = traceable(name="crisis_injection", tags=["crisis", "entropy"])(wrapper)

    return wrapper


def trace_monte_carlo_timeline(func: Callable) -> Callable:
    """Decorator: traces individual timeline with seed, severity, outcome.

    Tags: monte-carlo
    Metadata: seed, crisis_severity, reached_homeostasis, turns_total
    """
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        result = await func(self, *args, **kwargs)
        if _LANGSMITH_AVAILABLE and settings.langsmith_tracing:
            try:
                run = get_current_run_tree()
                if run:
                    run.add_metadata({
                        "seed": result.seed,
                        "crisis_severity": result.crisis_severity,
                        "reached_homeostasis": result.reached_homeostasis,
                        "turns_total": result.turns_total,
                        "antifragile": result.antifragile,
                    })
                    run.tags = list(set((run.tags or []) + ["monte-carlo"]))
            except Exception as exc:
                logger.debug("LangSmith trace_monte_carlo_timeline failed: %s", exc)
        return result

    if _LANGSMITH_AVAILABLE:
        wrapper = traceable(name="timeline_simulation", tags=["monte-carlo"])(wrapper)

    return wrapper


# ---------------------------------------------------------------------------
# Centralized observer
# ---------------------------------------------------------------------------


class AprioriObserver:
    """Centralized observability hub.

    Pushes simulation summaries to LangSmith as structured datasets.
    All methods are fire-and-forget — logging failures never break simulation.
    """

    def __init__(self) -> None:
        self._client: Client | None = None
        if _LANGSMITH_AVAILABLE and settings.langsmith_api_key:
            try:
                self._client = Client(api_key=settings.langsmith_api_key)
            except Exception as exc:
                logger.warning("Failed to initialize LangSmith client: %s", exc)

        self._collapse_log: List[Dict[str, Any]] = []
        self._timeline_log: List[Dict[str, Any]] = []
        self._convergence_log: List[Dict[str, Any]] = []

    def log_collapse_event(
        self, pair_id: str, turn: int, signals: Dict[str, Any]
    ) -> None:
        """Log a collapse risk assessment event."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "pair_id": pair_id,
            "turn": turn,
            "signals": signals,
        }
        self._collapse_log.append(entry)
        logger.info(
            "Collapse event: pair=%s turn=%d risk=%.3f level=%s",
            pair_id, turn,
            signals.get("overall_collapse_risk", 0.0),
            signals.get("risk_level", "UNKNOWN"),
        )

    def log_timeline_outcome(self, timeline_data: Dict[str, Any]) -> None:
        """Log a completed timeline result."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "seed": timeline_data.get("seed"),
            "pair_id": timeline_data.get("pair_id"),
            "crisis_severity": timeline_data.get("crisis_severity"),
            "reached_homeostasis": timeline_data.get("reached_homeostasis"),
            "antifragile": timeline_data.get("antifragile"),
            "turns_total": timeline_data.get("turns_total"),
        }
        self._timeline_log.append(entry)

    def log_linguistic_convergence(
        self, pair_id: str, convergence: Dict[str, Any]
    ) -> None:
        """Log a linguistic convergence measurement."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "pair_id": pair_id,
            "convergence": convergence,
        }
        self._convergence_log.append(entry)

    def create_evaluation_dataset(
        self, distribution_data: Dict[str, Any]
    ) -> str | None:
        """Push a simulation distribution to LangSmith as an evaluation dataset.

        Returns the dataset name if successful, None otherwise.
        """
        if not self._client:
            logger.debug("LangSmith client not available; skipping dataset creation")
            return None

        try:
            pair_id = distribution_data.get("pair_id", "unknown")
            dataset_name = f"apriori-eval-{pair_id}-{datetime.now(timezone.utc):%Y%m%d-%H%M}"

            dataset = self._client.create_dataset(
                dataset_name=dataset_name,
                description=f"APRIORI simulation results for pair {pair_id}",
            )

            timelines = distribution_data.get("timelines", [])
            for t in timelines[:50]:  # Limit to 50 examples
                self._client.create_example(
                    inputs={
                        "pair_id": t.get("pair_id"),
                        "crisis_severity": t.get("crisis_severity"),
                        "crisis_axis": t.get("crisis_axis"),
                    },
                    outputs={
                        "reached_homeostasis": t.get("reached_homeostasis"),
                        "narrative_elasticity": t.get("narrative_elasticity"),
                        "antifragile": t.get("antifragile"),
                        "turns_total": t.get("turns_total"),
                    },
                    dataset_id=dataset.id,
                )

            logger.info("Created LangSmith dataset: %s (%d examples)", dataset_name, min(len(timelines), 50))
            return dataset_name

        except Exception as exc:
            logger.warning("Failed to create LangSmith dataset: %s", exc)
            return None

    def get_collapse_log(self) -> List[Dict[str, Any]]:
        return list(self._collapse_log)

    def get_timeline_log(self) -> List[Dict[str, Any]]:
        return list(self._timeline_log)
