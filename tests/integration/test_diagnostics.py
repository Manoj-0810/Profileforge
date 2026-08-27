"""Integration tests for healthz and readyz diagnostics endpoints."""

from __future__ import annotations

import httpx
import pytest

from app.main import app


@pytest.mark.asyncio
async def test_healthz_endpoint():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/healthz")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
        assert resp.json()["service"] == "profileforge"


@pytest.mark.asyncio
async def test_readyz_endpoint():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/readyz")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ready"
        assert "cache_entries" in resp.json()
