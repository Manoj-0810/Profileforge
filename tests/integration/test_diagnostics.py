"""Integration tests for healthz, readyz, and OpenAPI schema documentation."""

from __future__ import annotations

import json

import httpx
import pytest

from app.config import settings
from app.main import app
from app.models import ProfileLookupRequest


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


@pytest.mark.asyncio
async def test_readyz_reports_unconfigured_live_provider(
    monkeypatch: pytest.MonkeyPatch,
):
    """Readiness should expose an actionable state when direct credentials are absent."""
    monkeypatch.setattr(settings, "EXTRACTOR_TYPE", "linkedin")
    monkeypatch.setattr(settings, "LINKEDIN_LI_AT", "")
    monkeypatch.setattr(settings, "LINKEDIN_JSESSIONID", "")

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/readyz")

    assert resp.status_code == 503
    assert resp.json()["status"] == "not_ready"
    assert resp.json()["provider_configured"] is False


@pytest.mark.asyncio
async def test_openapi_schema_request_examples_valid():
    """Verify that OpenAPI spec contains valid, parsable request examples for /v1/profile."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/openapi.json")
        assert resp.status_code == 200
        openapi = resp.json()

        profile_post = openapi["paths"]["/v1/profile"]["post"]
        content = profile_post["requestBody"]["content"]["application/json"]
        examples = content.get("examples", {})
        assert len(examples) > 0, "OpenAPI spec must define request body examples"

        for ex_name, ex_def in examples.items():
            val = ex_def["value"]
            # Must serialize and deserialize as valid JSON
            serialized = json.dumps(val)
            parsed = json.loads(serialized)
            req = ProfileLookupRequest.model_validate(parsed)
            assert req.url.startswith("https://www.linkedin.com/in/")

            # Test sending the exact OpenAPI example value to /v1/profile
            api_resp = await client.post(
                "/v1/profile",
                json=val,
                headers={"X-API-Key": settings.API_KEYS[0]},
            )
            assert api_resp.status_code == 200, (
                f"Example '{ex_name}' must succeed against API"
            )
            assert "profile" in api_resp.json()
