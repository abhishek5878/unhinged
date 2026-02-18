"""Tests for the waitlist API endpoints."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from apriori.api.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    """Async HTTP client hitting the FastAPI app directly."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_join_waitlist(client: AsyncClient):
    """Signing up should return a position and referral code."""
    response = await client.post(
        "/waitlist",
        json={
            "name": "Arjun Sharma",
            "email": "arjun@test.com",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "arjun@test.com"
    assert data["name"] == "Arjun Sharma"
    assert data["position"] >= 1
    assert len(data["referral_code"]) == 8
    assert data["status"] == "waiting"


@pytest.mark.asyncio
async def test_duplicate_email_rejected(client: AsyncClient):
    """Signing up with the same email twice should return 409."""
    payload = {"name": "Priya Kapoor", "email": "priya@test.com"}
    await client.post("/waitlist", json=payload)
    response = await client.post("/waitlist", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_join_with_partner_email(client: AsyncClient):
    """Signing up with a partner email should work."""
    response = await client.post(
        "/waitlist",
        json={
            "name": "Arjun Sharma",
            "email": "arjun-partner@test.com",
            "partner_email": "priya-partner@test.com",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["partner_email"] == "priya-partner@test.com"


@pytest.mark.asyncio
async def test_join_with_referral_code(client: AsyncClient):
    """Signing up with a referral code should be tracked."""
    response = await client.post(
        "/waitlist",
        json={
            "name": "Ravi Kumar",
            "email": "ravi@test.com",
            "referral_code_used": "ABC12345",
        },
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_position_lookup_by_email(client: AsyncClient):
    """Looking up position by email should work after signup."""
    await client.post(
        "/waitlist",
        json={"name": "Lookup Test", "email": "lookup@test.com"},
    )
    response = await client.get("/waitlist/position/lookup@test.com")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "lookup@test.com"
    assert data["position"] >= 1
    assert data["total_signups"] >= 1


@pytest.mark.asyncio
async def test_position_lookup_not_found(client: AsyncClient):
    """Looking up a non-existent email should return 404."""
    response = await client.get("/waitlist/position/nobody@test.com")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_me_requires_auth(client: AsyncClient):
    """GET /waitlist/me without auth should return 401 or 403."""
    response = await client.get("/waitlist/me")
    assert response.status_code in (401, 403)
