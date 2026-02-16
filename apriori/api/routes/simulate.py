"""Simulation API routes — launch, monitor, report, cancel Monte Carlo runs."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apriori.api.schemas import (
    SimulationCreateRequest,
    SimulationCreateResponse,
    SimulationProgressMessage,
    SimulationReportResponse,
    SimulationStatusResponse,
)
from apriori.config import settings
from apriori.core.monte_carlo import RelationalMonteCarlo
from apriori.db.models import SimulationRun, UserProfile
from apriori.db.session import get_session
from apriori.models.shadow_vector import AttachmentStyle, ShadowVector
from apriori.models.simulation import RelationalProbabilityDistribution
from apriori.workflows.simulation_workflow import AprioriSimulationWorkflow, SimulationInput

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _shadow_from_profile(profile: UserProfile) -> ShadowVector:
    """Reconstruct a ShadowVector from a stored profile's JSONB."""
    data = profile.shadow_vector
    return ShadowVector(
        agent_id=str(profile.id),
        values=data["values"],
        attachment_style=AttachmentStyle(data["attachment_style"]),
        fear_architecture=data.get("fear_architecture", []),
        linguistic_signature=data.get("linguistic_signature", []),
        entropy_tolerance=data.get("entropy_tolerance", 0.5),
        communication_style=data.get("communication_style", "direct"),
    )


async def _run_inline_simulation(
    simulation_id: UUID,
    shadow_a: ShadowVector,
    shadow_b: ShadowVector,
    pair_id: str,
    n_timelines: int,
    severity_range: tuple[float, float] | None,
    session_factory,
) -> None:
    """Background task: run Monte Carlo directly (no Temporal)."""
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(
        base_url=settings.vllm_base_url,
        model=settings.vllm_model_name,
        api_key="not-needed",
        temperature=0.7,
    )

    sev = severity_range or (0.05, 0.95)
    mc = RelationalMonteCarlo(
        llm_client=llm,
        n_timelines=n_timelines,
        severity_range=sev,
    )

    async with session_factory() as session:
        # Mark running
        run = await session.get(SimulationRun, simulation_id)
        if run:
            run.status = "running"
            await session.commit()

    try:
        dist = await mc.run_ensemble(shadow_a, shadow_b, pair_id)

        async with session_factory() as session:
            run = await session.get(SimulationRun, simulation_id)
            if run:
                run.status = "completed"
                run.results = json.loads(dist.model_dump_json())
                run.completed_at = datetime.now(timezone.utc)
                await session.commit()

    except Exception as exc:
        logger.error("Inline simulation %s failed: %s", simulation_id, exc)
        async with session_factory() as session:
            run = await session.get(SimulationRun, simulation_id)
            if run:
                run.status = "failed"
                run.completed_at = datetime.now(timezone.utc)
                await session.commit()


# ---------------------------------------------------------------------------
# POST /simulate
# ---------------------------------------------------------------------------


@router.post("", response_model=SimulationCreateResponse)
async def create_simulation(
    request: SimulationCreateRequest,
    req: Request,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
) -> SimulationCreateResponse:
    """Launch a new Monte Carlo relational simulation.

    If use_temporal is True (default for n>20), dispatches to the Temporal
    workflow for fault-tolerant execution. Otherwise runs inline as a
    background task.
    """
    # Load profiles
    user_a = await session.get(UserProfile, request.user_a_id)
    if not user_a:
        raise HTTPException(status_code=404, detail=f"User {request.user_a_id} not found")
    user_b = await session.get(UserProfile, request.user_b_id)
    if not user_b:
        raise HTTPException(status_code=404, detail=f"User {request.user_b_id} not found")

    shadow_a = _shadow_from_profile(user_a)
    shadow_b = _shadow_from_profile(user_b)
    pair_id = f"{user_a.id}_{user_b.id}"

    # Decide execution mode
    use_temporal = request.use_temporal
    if use_temporal is None:
        use_temporal = request.n_timelines > 20

    # Create SimulationRun record
    sim_id = uuid4()
    sim_run = SimulationRun(
        id=sim_id,
        pair_id=pair_id,
        user_a_id=request.user_a_id,
        user_b_id=request.user_b_id,
        status="queued",
        n_timelines=request.n_timelines,
    )

    # Estimate ETA (~3s per timeline for Temporal, ~5s inline)
    eta = int(request.n_timelines * (3 if use_temporal else 5))

    if use_temporal and req.app.state.temporal_client:
        workflow_id = f"apriori-sim-{sim_id}"
        sim_run.temporal_workflow_id = workflow_id
        session.add(sim_run)
        await session.commit()

        # Start Temporal workflow
        await req.app.state.temporal_client.start_workflow(
            AprioriSimulationWorkflow.run,
            SimulationInput(
                pair_id=pair_id,
                shadow_a_json=shadow_a.model_dump_json(),
                shadow_b_json=shadow_b.model_dump_json(),
                n_simulations=request.n_timelines,
                max_turns=settings.max_timeline_turns,
            ),
            id=workflow_id,
            task_queue=settings.temporal_task_queue,
        )
        status = "queued"
    else:
        session.add(sim_run)
        await session.commit()

        # Run as background task
        from apriori.db.session import async_session as session_factory
        background_tasks.add_task(
            _run_inline_simulation,
            sim_id,
            shadow_a,
            shadow_b,
            pair_id,
            request.n_timelines,
            request.crisis_severity_range,
            session_factory,
        )
        status = "running"

    return SimulationCreateResponse(
        simulation_id=sim_id,
        status=status,
        eta_seconds=eta,
    )


# ---------------------------------------------------------------------------
# GET /simulate/{simulation_id}
# ---------------------------------------------------------------------------


@router.get("/{simulation_id}", response_model=SimulationStatusResponse)
async def get_simulation(
    simulation_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> SimulationStatusResponse:
    """Retrieve simulation status and results if completed."""
    run = await session.get(SimulationRun, simulation_id)
    if not run:
        raise HTTPException(status_code=404, detail="Simulation not found")

    # If running via Temporal and not yet completed, try to fetch from Redis
    if run.status in ("queued", "running") and run.temporal_workflow_id and run.results is None:
        # Check Redis for completed results
        try:
            from apriori.db.session import async_session
            # Results may have been stored by the workflow
            redis_key = f"apriori:result:{run.pair_id}"
            # We'll check on next poll — don't block here
        except Exception:
            pass

    return SimulationStatusResponse(
        simulation_id=run.id,
        pair_id=run.pair_id,
        status=run.status,
        n_timelines=run.n_timelines,
        temporal_workflow_id=run.temporal_workflow_id,
        results=run.results,
        created_at=run.created_at,
        completed_at=run.completed_at,
    )


# ---------------------------------------------------------------------------
# GET /simulate/{simulation_id}/report
# ---------------------------------------------------------------------------


@router.get("/{simulation_id}/report", response_model=SimulationReportResponse)
async def get_simulation_report(
    simulation_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> SimulationReportResponse:
    """Generate executive report for a completed simulation."""
    run = await session.get(SimulationRun, simulation_id)
    if not run:
        raise HTTPException(status_code=404, detail="Simulation not found")
    if run.status != "completed" or run.results is None:
        raise HTTPException(status_code=409, detail="Simulation not yet completed")

    dist = RelationalProbabilityDistribution.model_validate(run.results)

    from langchain_openai import ChatOpenAI
    llm = ChatOpenAI(
        base_url=settings.vllm_base_url,
        model=settings.vllm_model_name,
        api_key="not-needed",
    )
    mc = RelationalMonteCarlo(llm_client=llm)
    report = mc.generate_executive_report(dist)

    return SimulationReportResponse(
        simulation_id=run.id,
        report=report,
    )


# ---------------------------------------------------------------------------
# WebSocket /simulate/{simulation_id}/progress
# ---------------------------------------------------------------------------


@router.websocket("/{simulation_id}/progress")
async def simulation_progress(
    websocket: WebSocket,
    simulation_id: UUID,
):
    """Stream live progress updates via WebSocket from Redis pub/sub."""
    await websocket.accept()

    # Look up pair_id for this simulation
    from apriori.db.session import async_session

    async with async_session() as session:
        run = await session.get(SimulationRun, simulation_id)
        if not run:
            await websocket.send_json({"error": "Simulation not found"})
            await websocket.close()
            return
        pair_id = run.pair_id

    redis = websocket.app.state.redis
    pubsub = redis.pubsub()
    channel = f"apriori:progress:{pair_id}"

    try:
        await pubsub.subscribe(channel)

        while True:
            message = await asyncio.wait_for(
                pubsub.get_message(ignore_subscribe_messages=True, timeout=2.0),
                timeout=5.0,
            )

            if message and message["type"] == "message":
                data = json.loads(message["data"])
                progress = SimulationProgressMessage(
                    completed=data["completed"],
                    total=data["total"],
                    status=data["status"],
                    percent=round(data["completed"] / max(1, data["total"]) * 100, 1),
                )
                await websocket.send_json(progress.model_dump())

                if data["status"] in ("completed", "cancelled", "failed"):
                    await websocket.close()
                    return
            else:
                # Send heartbeat
                await websocket.send_json({"heartbeat": True})

    except (WebSocketDisconnect, asyncio.TimeoutError):
        pass
    except Exception as exc:
        logger.error("WebSocket error: %s", exc)
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.aclose()


# ---------------------------------------------------------------------------
# POST /simulate/{simulation_id}/cancel
# ---------------------------------------------------------------------------


@router.post("/{simulation_id}/cancel")
async def cancel_simulation(
    simulation_id: UUID,
    req: Request,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Send cancellation signal to a running Temporal workflow."""
    run = await session.get(SimulationRun, simulation_id)
    if not run:
        raise HTTPException(status_code=404, detail="Simulation not found")
    if run.status not in ("queued", "running"):
        raise HTTPException(status_code=409, detail=f"Cannot cancel simulation in '{run.status}' state")

    if run.temporal_workflow_id and req.app.state.temporal_client:
        handle = req.app.state.temporal_client.get_workflow_handle(run.temporal_workflow_id)
        await handle.signal(AprioriSimulationWorkflow.cancel_simulation)

        run.status = "cancelled"
        run.completed_at = datetime.now(timezone.utc)
        await session.commit()

        return {"simulation_id": str(simulation_id), "status": "cancelled"}
    else:
        raise HTTPException(
            status_code=409,
            detail="Cannot cancel non-Temporal simulation (no workflow ID)",
        )
