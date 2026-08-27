"""Integration tests asserting standard error responses across failure modes."""

from __future__ import annotations

import httpx
import pytest

from app.config import settings
from app.main import app

AUTH_HEADERS = {"X-API-Key": settings.API_KEYS[0]}


@pytest.mark.asyncio
async def test_profile_not_found_response():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/v1/profile",
            json={"url": "https://www.linkedin.com/in/not-found-user"},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 404
        data = resp.json()
        assert "error" in data
        assert data["error"]["code"] == "PROFILE_NOT_FOUND"
        assert "not found" in data["error"]["message"].lower()


@pytest.mark.asyncio
async def test_upstream_auth_failed_response():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/v1/profile",
            json={"url": "https://www.linkedin.com/in/auth-fail-user"},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 502
        data = resp.json()
        assert data["error"]["code"] == "UPSTREAM_AUTH_FAILED"


@pytest.mark.asyncio
async def test_upstream_rate_limited_response():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/v1/profile",
            json={"url": "https://www.linkedin.com/in/rate-limit-user"},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 502
        data = resp.json()
        assert data["error"]["code"] == "UPSTREAM_RATE_LIMITED"


@pytest.mark.asyncio
async def test_upstream_timeout_response():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/v1/profile",
            json={"url": "https://www.linkedin.com/in/timeout-user"},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 504
        data = resp.json()
        assert data["error"]["code"] == "UPSTREAM_TIMEOUT"
