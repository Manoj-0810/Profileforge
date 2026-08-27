"""Integration tests verifying full HTTP API request pipeline."""

from __future__ import annotations

import httpx
import pytest

from app.config import settings
from app.main import app

AUTH_HEADERS = {"X-API-Key": settings.API_KEYS[0]}


@pytest.mark.asyncio
async def test_successful_profile_lookup():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        # First request: Cache MISS
        payload = {"url": "https://www.linkedin.com/in/sarah-jenkins-dev"}
        resp = await client.post("/v1/profile", json=payload, headers=AUTH_HEADERS)

        assert resp.status_code == 200
        data = resp.json()

        assert "profile" in data
        assert data["profile"]["full_name"] == "Sarah Jenkins"
        assert (
            data["profile"]["headline"]
            == "Staff Distributed Systems Engineer @ CloudScale"
        )
        assert len(data["profile"]["experience"]) == 2
        assert len(data["profile"]["education"]) == 2
        assert "Python" in data["profile"]["skills"]

        assert data["cache_hit"] is False
        assert "request_id" in data
        assert "data_quality" in data
        assert data["data_quality"]["completeness_score"] == 1.0
        assert resp.headers.get("X-Request-ID") == data["request_id"]

        # Second request: Cache HIT
        resp2 = await client.post("/v1/profile", json=payload, headers=AUTH_HEADERS)
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert data2["cache_hit"] is True
        assert data2["profile"]["full_name"] == "Sarah Jenkins"


@pytest.mark.asyncio
async def test_profile_lookup_unauthorized_missing_key():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/v1/profile",
            json={"url": "https://www.linkedin.com/in/sarah-jenkins-dev"},
        )
        assert resp.status_code == 401
        err = resp.json().get("error", {})
        assert err["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_profile_lookup_unauthorized_invalid_key():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/v1/profile",
            json={"url": "https://www.linkedin.com/in/sarah-jenkins-dev"},
            headers={"X-API-Key": "wrong-secret-key"},
        )
        assert resp.status_code == 401
        err = resp.json().get("error", {})
        assert err["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_profile_lookup_bad_url():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/v1/profile",
            json={"url": "https://google.com/not-linkedin"},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 400
        err = resp.json().get("error", {})
        assert err["code"] == "INVALID_PROFILE_URL"
