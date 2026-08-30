"""Security route coverage test asserting strict authentication across all application endpoints."""

from __future__ import annotations

import httpx
import pytest
from fastapi.routing import APIRoute

from app.config import settings
from app.main import app

UNAUTHENTICATED_ALLOWED_PATHS = {
    "/",
    "/healthz",
    "/readyz",
    "/docs",
    "/redoc",
    "/openapi.json",
}


@pytest.mark.asyncio
async def test_openapi_security_scheme_definition():
    """Verify that OpenAPI security scheme is explicitly declared and bound to protected endpoints."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/openapi.json")
        assert resp.status_code == 200
        openapi = resp.json()

        # Security scheme assertions
        security_schemes = openapi.get("components", {}).get("securitySchemes", {})
        assert "ProfileForgeApiKey" in security_schemes, (
            "OpenAPI must declare security scheme 'ProfileForgeApiKey'"
        )

        scheme = security_schemes["ProfileForgeApiKey"]
        assert scheme["type"] == "apiKey"
        assert scheme["name"] == "X-API-Key"
        assert scheme["in"] == "header"

        # Protected route assertions
        profile_op = openapi["paths"]["/v1/profile"]["post"]
        assert "security" in profile_op, (
            "POST /v1/profile must declare security requirement"
        )
        assert any("ProfileForgeApiKey" in s for s in profile_op["security"]), (
            "POST /v1/profile must require 'ProfileForgeApiKey'"
        )

        # Public route assertions (no security requirement)
        health_op = openapi["paths"]["/healthz"]["get"]
        assert "security" not in health_op or len(health_op.get("security", [])) == 0


@pytest.mark.asyncio
async def test_all_endpoints_enforce_authentication():
    """Dynamically enumerate all registered FastAPI routes and assert authentication requirements."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        for route in app.routes:
            if not isinstance(route, APIRoute):
                continue

            path = route.path
            methods = [m for m in route.methods if m not in {"HEAD", "OPTIONS"}]

            for method in methods:
                if path in UNAUTHENTICATED_ALLOWED_PATHS:
                    # Permitted public paths
                    if method == "GET":
                        resp = await client.get(path)
                        assert resp.status_code in {200, 307}, (
                            f"Public endpoint {path} returned {resp.status_code}"
                        )
                    continue

                # For every other route, test with NO API key
                request_kwargs: dict = {}
                if method == "POST":
                    request_kwargs["json"] = {
                        "url": "https://www.linkedin.com/in/sarah-jenkins"
                    }

                resp_unauth = await client.request(method, path, **request_kwargs)
                assert resp_unauth.status_code == 401, (
                    f"Security Violation: Endpoint {method} {path} is missing authentication! (Returned {resp_unauth.status_code})"
                )

                # Test with INVALID API key
                resp_invalid = await client.request(
                    method,
                    path,
                    headers={"X-API-Key": "invalid-secret-key-attacker"},
                    **request_kwargs,
                )
                assert resp_invalid.status_code == 401, (
                    f"Security Violation: Endpoint {method} {path} accepted an invalid API key!"
                )

                # Test with VALID API key
                resp_valid = await client.request(
                    method,
                    path,
                    headers={"X-API-Key": settings.API_KEYS[0]},
                    **request_kwargs,
                )
                assert resp_valid.status_code == 200, (
                    f"Endpoint {method} {path} failed with valid API key! (Returned {resp_valid.status_code})"
                )


@pytest.mark.asyncio
async def test_zero_secret_leakage_in_error_and_success_payloads():
    """Assert that configured tokens and secret keys never leak in response payloads."""
    configured_secrets = [
        settings.LINKEDIN_LI_AT,
        settings.LINKEDIN_JSESSIONID,
    ]
    # Filter out empty strings
    active_secrets = [s for s in configured_secrets if s]

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        # 1. Test unauthenticated error response
        resp_unauth = await client.post(
            "/v1/profile", json={"url": "https://www.linkedin.com/in/sarah-jenkins"}
        )
        for secret in active_secrets:
            assert secret not in resp_unauth.text

        # 2. Test authenticated success response
        resp_auth = await client.post(
            "/v1/profile",
            headers={"X-API-Key": settings.API_KEYS[0]},
            json={"url": "https://www.linkedin.com/in/sarah-jenkins"},
        )
        for secret in active_secrets:
            assert secret not in resp_auth.text
