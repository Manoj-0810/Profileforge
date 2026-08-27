"""Unit tests for LinkedAPIClient polling lifecycle, error classification, and timeouts."""

from __future__ import annotations

import httpx
import pytest

from app.errors import ErrorCode, ProfileForgeError
from app.providers.linkedapi.client import LinkedAPIClient


@pytest.mark.asyncio
async def test_missing_credentials_raises_503():
    client = LinkedAPIClient(api_token="", identification_token="")
    with pytest.raises(ProfileForgeError) as exc_info:
        await client.execute_profile_workflow("https://www.linkedin.com/in/test")
    assert exc_info.value.error_code == ErrorCode.AUTH_CONFIGURATION_ERROR
    assert exc_info.value.status_code == 503


@pytest.mark.asyncio
async def test_successful_submit_and_poll():
    # Mock transport simulating submit -> pending -> completed
    poll_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal poll_count
        if request.method == "POST" and "/workflows" in str(request.url):
            return httpx.Response(
                200,
                json={
                    "success": True,
                    "result": {
                        "workflowId": "wf-test-123",
                        "workflowStatus": "pending",
                    },
                },
            )
        if request.method == "GET" and "/workflows/wf-test-123" in str(request.url):
            poll_count += 1
            if poll_count == 1:
                return httpx.Response(
                    200,
                    json={
                        "success": True,
                        "result": {
                            "workflowStatus": "running",
                        },
                    },
                )
            return httpx.Response(
                200,
                json={
                    "success": True,
                    "result": {
                        "workflowStatus": "completed",
                        "completion": {
                            "success": True,
                            "data": {
                                "name": "Sarah Jenkins",
                                "headline": "Staff Engineer",
                            },
                        },
                    },
                },
            )
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = LinkedAPIClient(
            api_token="valid_token",
            identification_token="valid_ident",
            poll_interval_seconds=0.01,
            http_client=http_client,
        )
        result = await client.execute_profile_workflow(
            "https://www.linkedin.com/in/sarah-jenkins"
        )
        assert result["success"] is True
        assert result["data"]["name"] == "Sarah Jenkins"
        assert poll_count == 2


@pytest.mark.asyncio
async def test_person_not_found_error_mapped_to_404():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            return httpx.Response(
                200,
                json={"success": True, "result": {"workflowId": "wf-404"}},
            )
        return httpx.Response(
            200,
            json={
                "success": True,
                "result": {
                    "workflowStatus": "completed",
                    "completion": {
                        "success": False,
                        "error": {
                            "type": "personNotFound",
                            "message": "Person profile not found",
                        },
                    },
                },
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = LinkedAPIClient(
            api_token="valid_token",
            identification_token="valid_ident",
            poll_interval_seconds=0.01,
            http_client=http_client,
        )
        with pytest.raises(ProfileForgeError) as exc_info:
            await client.execute_profile_workflow(
                "https://www.linkedin.com/in/notfound"
            )
        assert exc_info.value.error_code == ErrorCode.PROFILE_NOT_FOUND
        assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_account_signed_out_mapped_to_502():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            return httpx.Response(
                200,
                json={"success": True, "result": {"workflowId": "wf-signedout"}},
            )
        return httpx.Response(
            200,
            json={
                "success": True,
                "result": {
                    "workflowStatus": "failed",
                    "failure": {
                        "reason": "linkedinAccountSignedOut",
                        "message": "Account signed out",
                    },
                },
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = LinkedAPIClient(
            api_token="valid_token",
            identification_token="valid_ident",
            poll_interval_seconds=0.01,
            http_client=http_client,
        )
        with pytest.raises(ProfileForgeError) as exc_info:
            await client.execute_profile_workflow("https://www.linkedin.com/in/test")
        assert exc_info.value.error_code == ErrorCode.UPSTREAM_AUTH_FAILED
        assert exc_info.value.status_code == 502


@pytest.mark.asyncio
async def test_polling_timeout_mapped_to_504():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            return httpx.Response(
                200,
                json={"success": True, "result": {"workflowId": "wf-slow"}},
            )
        if request.method == "DELETE":
            return httpx.Response(
                200, json={"success": True, "result": {"cancelled": True}}
            )
        # Always return running
        return httpx.Response(
            200,
            json={"success": True, "result": {"workflowStatus": "running"}},
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = LinkedAPIClient(
            api_token="valid_token",
            identification_token="valid_ident",
            timeout_seconds=0.05,
            poll_interval_seconds=0.01,
            http_client=http_client,
        )
        with pytest.raises(ProfileForgeError) as exc_info:
            await client.execute_profile_workflow("https://www.linkedin.com/in/test")
        assert exc_info.value.error_code == ErrorCode.UPSTREAM_TIMEOUT
        assert exc_info.value.status_code == 504
