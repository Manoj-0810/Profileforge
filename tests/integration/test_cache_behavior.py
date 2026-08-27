"""Integration tests verifying URL variation canonicalization and cache-hit behavior."""

from __future__ import annotations

import httpx
import pytest

from app.config import settings
from app.main import app

AUTH_HEADERS = {"X-API-Key": settings.API_KEYS[0]}


@pytest.mark.asyncio
async def test_url_variations_hit_same_cache_entry():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Request 1: standard URL
        r1 = await client.post(
            "/v1/profile",
            json={"url": "https://www.linkedin.com/in/alex-mercer-tech"},
            headers=AUTH_HEADERS,
        )
        assert r1.status_code == 200
        assert r1.json()["cache_hit"] is False

        # Request 2: trailing slash + uppercase
        r2 = await client.post(
            "/v1/profile",
            json={"url": "https://www.linkedin.com/in/ALEX-MERCER-TECH/"},
            headers=AUTH_HEADERS,
        )
        assert r2.status_code == 200
        assert r2.json()["cache_hit"] is True

        # Request 3: http + query params
        r3 = await client.post(
            "/v1/profile",
            json={"url": "http://linkedin.com/in/alex-mercer-tech?trackingId=99"},
            headers=AUTH_HEADERS,
        )
        assert r3.status_code == 200
        assert r3.json()["cache_hit"] is True
