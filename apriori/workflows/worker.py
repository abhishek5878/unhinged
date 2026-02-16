"""Temporal worker entrypoint.

Registers all workflow classes and activity functions, then starts
the worker connected to the configured Temporal server.
"""

from __future__ import annotations

import asyncio
import logging

from temporalio.client import Client
from temporalio.worker import Worker

from apriori.config import settings
from apriori.workflows.simulation_workflow import (
    AprioriSimulationWorkflow,
    notify_progress_activity,
    run_timeline_batch_activity,
    store_results_activity,
)

logger = logging.getLogger(__name__)


async def run_worker() -> None:
    """Start the Temporal worker with all registered workflows and activities."""
    logger.info(
        "Connecting to Temporal at %s (namespace=%s, queue=%s)",
        settings.temporal_host,
        settings.temporal_namespace,
        settings.temporal_task_queue,
    )

    client = await Client.connect(
        settings.temporal_host,
        namespace=settings.temporal_namespace,
    )

    worker = Worker(
        client,
        task_queue=settings.temporal_task_queue,
        workflows=[AprioriSimulationWorkflow],
        activities=[
            run_timeline_batch_activity,
            notify_progress_activity,
            store_results_activity,
        ],
    )

    logger.info("Worker started. Listening on queue: %s", settings.temporal_task_queue)
    await worker.run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_worker())
