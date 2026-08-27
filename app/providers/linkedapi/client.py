"""LinkedAPI HTTP client managing workflow submission, polling, retries, and errors."""

from __future__ import annotations

import asyncio
import random
from typing import Any

import httpx
import structlog

from app.errors import ErrorCode, ProfileForgeError

logger = structlog.get_logger(__name__)


class LinkedAPIClient:
    """HTTP client communicating with api.linkedapi.io."""

    BASE_URL = "https://api.linkedapi.io"

    def __init__(
        self,
        api_token: str | None = None,
        identification_token: str | None = None,
        timeout_seconds: float = 120.0,
        poll_interval_seconds: float = 3.0,
        max_retries: int = 3,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.api_token = api_token or ""
        self.identification_token = identification_token or ""
        self.timeout_seconds = timeout_seconds
        self.poll_interval_seconds = poll_interval_seconds
        self.max_retries = max_retries
        self._external_client = http_client

    def _get_headers(self) -> dict[str, str]:
        if not self.api_token or not self.identification_token:
            raise ProfileForgeError(
                ErrorCode.AUTH_CONFIGURATION_ERROR,
                "LinkedAPI credentials not configured. Set LINKEDAPI_TOKEN and LINKEDAPI_IDENTIFICATION_TOKEN.",
                status_code=503,
            )
        return {
            "linked-api-token": self.api_token,
            "identification-token": self.identification_token,
            "Content-Type": "application/json",
        }

    def _classify_error_response(self, error_dict: dict[str, Any]) -> ProfileForgeError:
        error_type = error_dict.get("type", "")
        message = error_dict.get("message", "Upstream provider error")

        if error_type in {
            "linkedApiTokenRequired",
            "invalidLinkedApiToken",
            "identificationTokenRequired",
            "invalidIdentificationToken",
            "subscriptionRequired",
        }:
            return ProfileForgeError(
                ErrorCode.AUTH_CONFIGURATION_ERROR, message, status_code=503
            )

        if error_type in {"tooManyRequests", "limitExceeded"}:
            return ProfileForgeError(
                ErrorCode.UPSTREAM_RATE_LIMITED, message, status_code=502
            )

        if error_type == "personNotFound":
            return ProfileForgeError(
                ErrorCode.PROFILE_NOT_FOUND, message, status_code=404
            )

        if error_type == "outsideWorkingHours":
            return ProfileForgeError(
                ErrorCode.UPSTREAM_CHALLENGE_DETECTED, message, status_code=502
            )

        return ProfileForgeError(
            ErrorCode.UPSTREAM_SERVER_ERROR, f"{error_type}: {message}", status_code=502
        )

    def _classify_failure_reason(
        self, failure_dict: dict[str, Any]
    ) -> ProfileForgeError:
        reason = failure_dict.get("reason", "")
        message = failure_dict.get("message", "Workflow execution failed")

        if reason == "linkedinAccountSignedOut":
            return ProfileForgeError(
                ErrorCode.UPSTREAM_AUTH_FAILED,
                f"LinkedIn account disconnected or signed out: {message}",
                status_code=502,
            )
        if reason == "languageNotSupported":
            return ProfileForgeError(
                ErrorCode.PROFILE_INACCESSIBLE,
                f"Target profile language not supported: {message}",
                status_code=502,
            )

        return ProfileForgeError(
            ErrorCode.UPSTREAM_SERVER_ERROR,
            f"Failure {reason}: {message}",
            status_code=502,
        )

    async def _send_request_with_retry(
        self,
        client: httpx.AsyncClient,
        method: str,
        url: str,
        headers: dict[str, str],
        json_data: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Executes an HTTP request with exponential backoff on transient network errors."""
        last_err: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=json_data,
                    timeout=30.0,
                )
                # Transient 5xx status codes retry
                if (
                    response.status_code in {502, 503, 504}
                    and attempt < self.max_retries - 1
                ):
                    backoff = (2**attempt) * 0.5 + random.uniform(0, 0.1)
                    await asyncio.sleep(backoff)
                    continue
                return response
            except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ConnectError) as exc:
                last_err = exc
                if attempt < self.max_retries - 1:
                    backoff = (2**attempt) * 0.5 + random.uniform(0, 0.1)
                    logger.warning(
                        "linkedapi_transient_retry",
                        attempt=attempt,
                        error=str(exc),
                        backoff=backoff,
                    )
                    await asyncio.sleep(backoff)
                else:
                    break

        raise ProfileForgeError(
            ErrorCode.UPSTREAM_SERVER_ERROR,
            f"Failed to communicate with LinkedAPI after {self.max_retries} attempts: {last_err}",
            status_code=502,
        )

    async def execute_profile_workflow(self, canonical_url: str) -> dict[str, Any]:
        """Submit a profile extraction workflow and poll until completion."""
        headers = self._get_headers()
        workflow_payload = {
            "actionType": "st.openPersonPage",
            "personUrl": canonical_url,
            "basicInfo": True,
            "then": [
                {"actionType": "st.retrievePersonExperience"},
                {"actionType": "st.retrievePersonEducation"},
                {"actionType": "st.retrievePersonSkills"},
                {"actionType": "st.retrievePersonLanguages"},
            ],
        }

        client = self._external_client or httpx.AsyncClient()
        should_close = self._external_client is None

        try:
            # 1. Submit workflow
            submit_url = f"{self.BASE_URL}/workflows"
            response = await self._send_request_with_retry(
                client, "POST", submit_url, headers=headers, json_data=workflow_payload
            )

            try:
                submit_data = response.json()
            except Exception as exc:
                raise ProfileForgeError(
                    ErrorCode.UPSTREAM_SERVER_ERROR,
                    f"Invalid JSON from LinkedAPI workflow submission (status {response.status_code})",
                    status_code=502,
                ) from exc

            if not submit_data.get("success", False):
                err = submit_data.get("error", {})
                raise self._classify_error_response(err)

            result = submit_data.get("result", {})
            workflow_id = result.get("workflowId")
            if not workflow_id:
                raise ProfileForgeError(
                    ErrorCode.UPSTREAM_SCHEMA_CHANGED,
                    "LinkedAPI response missing 'workflowId' in submission result",
                    status_code=502,
                )

            # 2. Polling loop
            start_time = asyncio.get_event_loop().time()
            poll_url = f"{self.BASE_URL}/workflows/{workflow_id}"

            while True:
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed >= self.timeout_seconds:
                    # Attempt best-effort cancellation
                    try:
                        await client.delete(poll_url, headers=headers, timeout=5.0)
                    except (httpx.HTTPError, asyncio.TimeoutError) as cancel_exc:
                        logger.debug(
                            "workflow_cancellation_failed", error=str(cancel_exc)
                        )
                    raise ProfileForgeError(
                        ErrorCode.UPSTREAM_TIMEOUT,
                        f"Upstream profile lookup timed out after {self.timeout_seconds:.1f}s",
                        status_code=504,
                    )

                await asyncio.sleep(self.poll_interval_seconds)

                poll_resp = await self._send_request_with_retry(
                    client, "GET", poll_url, headers=headers
                )
                try:
                    poll_data = poll_resp.json()
                except Exception as exc:
                    raise ProfileForgeError(
                        ErrorCode.UPSTREAM_SERVER_ERROR,
                        f"Invalid JSON while polling LinkedAPI workflow {workflow_id}",
                        status_code=502,
                    ) from exc

                if not poll_data.get("success", False):
                    err = poll_data.get("error", {})
                    raise self._classify_error_response(err)

                poll_result = poll_data.get("result", {})
                status = poll_result.get("workflowStatus")

                if status == "pending":
                    reason = poll_result.get("pendingReason")
                    if reason == "outsideWorkingHours":
                        raise ProfileForgeError(
                            ErrorCode.UPSTREAM_CHALLENGE_DETECTED,
                            f"Account is outside configured working hours: {poll_result.get('message')}",
                            status_code=502,
                        )
                    continue

                if status == "running":
                    continue

                if status == "failed":
                    failure = poll_result.get("failure", {})
                    raise self._classify_failure_reason(failure)

                if status == "completed":
                    completion = poll_result.get("completion", {})
                    if not completion.get("success", False):
                        err = completion.get("error", {})
                        raise self._classify_error_response(err)
                    return completion

                logger.warning(
                    "unknown_workflow_status", status=status, workflow_id=workflow_id
                )

        finally:
            if should_close:
                await client.aclose()
