"""FastAPI application with lifespan, CORS, and logging middleware."""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from temporalio.client import Client as TemporalClient

from apriori.api.routes import profiles, simulate
from apriori.config import settings
from apriori.db.session import engine, init_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: init DB, Redis, Temporal on startup; cleanup on shutdown."""
    # --- Startup ---
    logger.info("Initializing database (pgvector + tables)…")
    await init_db()

    logger.info("Connecting to Redis at %s…", settings.redis_url)
    app.state.redis = aioredis.from_url(
        settings.redis_url, decode_responses=True
    )

    try:
        logger.info("Connecting to Temporal at %s…", settings.temporal_host)
        app.state.temporal_client = await TemporalClient.connect(
            settings.temporal_host,
            namespace=settings.temporal_namespace,
        )
    except Exception as exc:
        logger.warning("Temporal connection failed (workflows unavailable): %s", exc)
        app.state.temporal_client = None

    logger.info("APRIORI API ready")

    yield

    # --- Shutdown ---
    logger.info("Shutting down…")
    await app.state.redis.aclose()
    await engine.dispose()
    logger.info("Shutdown complete")


app = FastAPI(
    title="APRIORI",
    description="Relational Foundation Model API — predicts long-term relational "
    "homeostasis via Recursive Theory of Mind and Monte Carlo trajectory analysis.",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS (permissive for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log request method, path, status, and duration."""
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s → %d (%.1fms)",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


# Routers
app.include_router(simulate.router, prefix="/simulate", tags=["simulation"])
app.include_router(profiles.router, prefix="/profiles", tags=["profiles"])


@app.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok"}
