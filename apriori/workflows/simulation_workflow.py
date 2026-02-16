"""Temporal durable workflow for long-running Monte Carlo simulations.

Provides fault-tolerant orchestration with:
- Batched timeline execution (10 per activity)
- Retry policies with exponential backoff
- Progress query handler
- Cancellation signal
- Redis pub/sub progress notifications
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any, Dict, List, Optional

from temporalio import activity, workflow

with workflow.unsafe.imports_passed_through():
    import redis.asyncio as aioredis

    from apriori.agents.dialogue_graph import run_simulation
    from apriori.config import settings
    from apriori.core.event_generator import StochasticEventGenerator
    from apriori.models.shadow_vector import ShadowVector
    from apriori.models.simulation import RelationalProbabilityDistribution, TimelineResult

logger = logging.getLogger(__name__)

BATCH_SIZE = 10


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class SimulationInput:
    """Input for a simulation workflow run."""

    pair_id: str
    shadow_a_json: str
    shadow_b_json: str
    n_simulations: int = 100
    max_turns: int = 50
    crisis_turn_min: int = 10
    crisis_turn_max: int = 25


@dataclass
class TimelineBatchInput:
    """Input for a batch of timeline simulations."""

    shadow_a_json: str
    shadow_b_json: str
    pair_id: str
    max_turns: int
    seeds: List[int] = field(default_factory=list)
    crisis_turns: List[int] = field(default_factory=list)


@dataclass
class ProgressUpdate:
    """Progress notification payload."""

    pair_id: str
    completed: int
    total: int
    status: str = "running"


# ---------------------------------------------------------------------------
# Activities
# ---------------------------------------------------------------------------


@activity.defn
async def run_timeline_batch_activity(batch_input: TimelineBatchInput) -> List[str]:
    """Run a batch of timeline simulations.

    Each batch processes up to BATCH_SIZE timelines sequentially within the
    activity. Returns serialized TimelineResult JSON strings.

    Timeout: 10 minutes per batch.
    """
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(
        base_url=settings.vllm_base_url,
        model=settings.vllm_model_name,
        api_key="not-needed",
        temperature=0.7,
    )
    event_gen = StochasticEventGenerator(llm)

    shadow_a = ShadowVector.model_validate_json(batch_input.shadow_a_json)
    shadow_b = ShadowVector.model_validate_json(batch_input.shadow_b_json)

    results: List[str] = []
    for seed, crisis_turn in zip(batch_input.seeds, batch_input.crisis_turns):
        activity.heartbeat(f"Running timeline seed={seed}")
        try:
            timeline = await run_simulation(
                shadow_a=shadow_a,
                shadow_b=shadow_b,
                llm_client=llm,
                event_generator=event_gen,
                max_turns=batch_input.max_turns,
                crisis_at_turn=crisis_turn,
                seed=seed,
            )
            results.append(timeline.model_dump_json())
        except Exception as exc:
            logger.error("Timeline seed=%d failed: %s", seed, exc)
            failed = TimelineResult(
                seed=seed,
                pair_id=batch_input.pair_id,
                crisis_severity=0.0,
                crisis_axis="unknown",
                reached_homeostasis=False,
                narrative_elasticity=0.0,
                final_resilience_score=0.0,
                antifragile=False,
                turns_total=0,
                belief_collapse_events=0,
                linguistic_convergence_final=0.0,
            )
            results.append(failed.model_dump_json())

    return results


@activity.defn
async def notify_progress_activity(update: ProgressUpdate) -> None:
    """Publish progress update via Redis pub/sub."""
    try:
        r = aioredis.from_url(settings.redis_url)
        payload = json.dumps({
            "pair_id": update.pair_id,
            "completed": update.completed,
            "total": update.total,
            "status": update.status,
        })
        await r.publish(f"apriori:progress:{update.pair_id}", payload)
        await r.aclose()
    except Exception as exc:
        logger.warning("Failed to publish progress: %s", exc)


@activity.defn
async def store_results_activity(pair_id: str, distribution_json: str) -> str:
    """Store the final distribution to Redis for retrieval by API."""
    try:
        r = aioredis.from_url(settings.redis_url)
        key = f"apriori:result:{pair_id}"
        await r.set(key, distribution_json, ex=86400)  # 24h TTL
        await r.aclose()
        return key
    except Exception as exc:
        logger.error("Failed to store results: %s", exc)
        return ""


# ---------------------------------------------------------------------------
# Workflow
# ---------------------------------------------------------------------------


@workflow.defn
class AprioriSimulationWorkflow:
    """Temporal workflow for running a full Monte Carlo simulation.

    Splits N timelines into batches of 10, executes each batch as a
    retryable activity, and aggregates results into a
    ``RelationalProbabilityDistribution``.

    Query handlers:
    - ``get_progress``: returns current completion count

    Signal handlers:
    - ``cancel_simulation``: gracefully cancels remaining batches
    """

    def __init__(self) -> None:
        self._completed = 0
        self._total = 0
        self._cancelled = False
        self._status = "initializing"
        self._pair_id = ""

    @workflow.run
    async def run(self, input: SimulationInput) -> str:
        """Execute the simulation and return the Redis result key."""
        import random as _random

        self._pair_id = input.pair_id
        self._total = input.n_simulations
        self._status = "running"

        retry_policy = workflow.RetryPolicy(
            initial_interval=timedelta(seconds=5),
            maximum_attempts=3,
            backoff_coefficient=2.0,
        )

        # Generate parameter sets
        rng = _random.Random(42)
        all_seeds = list(range(1, input.n_simulations + 1))
        all_crisis_turns = [
            rng.randint(input.crisis_turn_min, input.crisis_turn_max)
            for _ in range(input.n_simulations)
        ]

        # Split into batches
        all_results: List[str] = []
        for batch_start in range(0, input.n_simulations, BATCH_SIZE):
            if self._cancelled:
                self._status = "cancelled"
                break

            batch_end = min(batch_start + BATCH_SIZE, input.n_simulations)
            batch_input = TimelineBatchInput(
                shadow_a_json=input.shadow_a_json,
                shadow_b_json=input.shadow_b_json,
                pair_id=input.pair_id,
                max_turns=input.max_turns,
                seeds=all_seeds[batch_start:batch_end],
                crisis_turns=all_crisis_turns[batch_start:batch_end],
            )

            batch_results = await workflow.execute_activity(
                run_timeline_batch_activity,
                batch_input,
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=retry_policy,
                heartbeat_timeout=timedelta(minutes=2),
            )

            all_results.extend(batch_results)
            self._completed = len(all_results)

            # Notify progress (fire-and-forget, short timeout, no retry)
            await workflow.execute_activity(
                notify_progress_activity,
                ProgressUpdate(
                    pair_id=input.pair_id,
                    completed=self._completed,
                    total=self._total,
                    status=self._status,
                ),
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=workflow.RetryPolicy(maximum_attempts=1),
            )

        # Aggregate results
        timelines = [
            TimelineResult.model_validate_json(r) for r in all_results
        ]
        distribution = RelationalProbabilityDistribution(
            pair_id=input.pair_id,
            n_simulations=len(timelines),
            timelines=timelines,
        )

        # Store to Redis
        result_key = await workflow.execute_activity(
            store_results_activity,
            args=[input.pair_id, distribution.model_dump_json()],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=workflow.RetryPolicy(maximum_attempts=2),
        )

        # Final progress notification
        self._status = "completed"
        await workflow.execute_activity(
            notify_progress_activity,
            ProgressUpdate(
                pair_id=input.pair_id,
                completed=self._completed,
                total=self._total,
                status="completed",
            ),
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=workflow.RetryPolicy(maximum_attempts=1),
        )

        return result_key

    @workflow.query
    def get_progress(self) -> Dict[str, Any]:
        """Return current simulation progress."""
        return {
            "pair_id": self._pair_id,
            "completed": self._completed,
            "total": self._total,
            "status": self._status,
            "percent": (
                round(self._completed / self._total * 100, 1)
                if self._total > 0
                else 0.0
            ),
        }

    @workflow.signal
    async def cancel_simulation(self) -> None:
        """Signal to gracefully cancel remaining simulation batches."""
        self._cancelled = True
        self._status = "cancelling"
