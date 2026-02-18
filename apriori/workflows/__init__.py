"""Temporal workflow exports — lazy-loaded to avoid langgraph import chain."""

__all__ = [
    "AprioriSimulationWorkflow",
    "SimulationInput",
    "run_timeline_batch_activity",
    "notify_progress_activity",
    "store_results_activity",
]


def __getattr__(name: str):
    if name in __all__:
        from apriori.workflows.simulation_workflow import (
            AprioriSimulationWorkflow,
            SimulationInput,
            run_timeline_batch_activity,
            notify_progress_activity,
            store_results_activity,
        )
        _exports = {
            "AprioriSimulationWorkflow": AprioriSimulationWorkflow,
            "SimulationInput": SimulationInput,
            "run_timeline_batch_activity": run_timeline_batch_activity,
            "notify_progress_activity": notify_progress_activity,
            "store_results_activity": store_results_activity,
        }
        return _exports[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
