"""Unit tests for direct LinkedIn HTTP client and request builder."""

from __future__ import annotations

import httpx
import pytest

from app.errors import ErrorCode, ProfileForgeError
from app.providers.linkedin.client import (
    DEFAULT_DECORATION_ID,
    LinkedInClient,
    LinkedInRequestBuilder,
)


def test_request_builder_url_and_headers():
    """Verify request builder produces valid URLs, CSRF headers, and cookies."""
    url = LinkedInRequestBuilder.build_profile_url("sarah-jenkins-dev")
    assert "memberIdentity=sarah-jenkins-dev" in url
    assert DEFAULT_DECORATION_ID in url

    headers = LinkedInRequestBuilder.build_headers(
        jsessionid='"ajax:1234567890"', user_agent="TestAgent/1.0"
    )
    assert headers["csrf-token"] == "ajax:1234567890"
    assert headers["x-restli-protocol-version"] == "2.0.0"
    assert headers["accept"] == "application/vnd.linkedin.normalized+json+2.1"
    assert headers["user-agent"] == "TestAgent/1.0"
    assert "referer" not in headers
    assert "sec-ch-ua" not in headers

    cookies = LinkedInRequestBuilder.build_cookies("test-li-at", '"ajax:1234567890"')
    assert cookies["li_at"] == "test-li-at"
    assert cookies["JSESSIONID"] == '"ajax:1234567890"'


@pytest.mark.asyncio
async def test_client_missing_credentials_raises_error():
    """Verify client raises 503 AUTH_CONFIGURATION_ERROR if li_at cookie is missing."""
    client = LinkedInClient(li_at="", jsessionid="")
    with pytest.raises(ProfileForgeError) as exc_info:
        await client.fetch_profile_raw("sarah-jenkins")
    assert exc_info.value.error_code == ErrorCode.AUTH_CONFIGURATION_ERROR
    assert exc_info.value.status_code == 503


@pytest.mark.asyncio
async def test_client_successful_200_response():
    """Verify client returns parsed JSON dict on HTTP 200."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers.get("csrf-token") == "ajax:123"
        assert request.url.host == "www.linkedin.com"
        assert request.url.path == "/voyager/api/identity/dash/profiles"
        assert request.url.params["q"] == "memberIdentity"
        assert request.url.params["memberIdentity"] == "sarah-jenkins"
        assert request.url.params["decorationId"] == DEFAULT_DECORATION_ID
        assert "li_at=valid-li-at" in request.headers.get("cookie", "")
        assert "JSESSIONID=ajax:123" in request.headers.get("cookie", "")
        return httpx.Response(
            200, json={"included": [{"$type": "Profile", "firstName": "Sarah"}]}
        )

    transport = httpx.MockTransport(handler)
    mock_http = httpx.AsyncClient(transport=transport)
    client = LinkedInClient(
        li_at="valid-li-at", jsessionid="ajax:123", http_client=mock_http
    )

    result = await client.fetch_profile_raw("sarah-jenkins")
    assert "included" in result
    assert result["included"][0]["firstName"] == "Sarah"


@pytest.mark.asyncio
async def test_client_uses_rotated_session_cookie_and_csrf_on_next_lookup():
    """Verify upstream JSESSIONID rotation is reused without duplicate cookies."""
    requests: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(
            (
                request.headers.get("cookie", ""),
                request.headers.get("csrf-token", ""),
            )
        )
        if len(requests) == 1:
            return httpx.Response(
                200,
                headers={"set-cookie": "JSESSIONID=ajax:rotated; Path=/"},
                json={"included": [{"$type": "Profile", "firstName": "Sarah"}]},
            )
        return httpx.Response(
            200, json={"included": [{"$type": "Profile", "firstName": "Sarah"}]}
        )

    mock_http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    client = LinkedInClient(
        li_at="valid-li-at", jsessionid="ajax:original", http_client=mock_http
    )

    await client.fetch_profile_raw("sarah-jenkins")
    await client.fetch_profile_raw("sarah-jenkins")

    assert "JSESSIONID=ajax:original" in requests[0][0]
    assert "li_at=valid-li-at" in requests[0][0]
    assert requests[0][1] == "ajax:original"
    assert "JSESSIONID=ajax:rotated" in requests[1][0]
    assert "JSESSIONID=ajax:original" not in requests[1][0]
    assert requests[1][1] == "ajax:rotated"


@pytest.mark.asyncio
async def test_client_handles_401_and_403_auth_failures():
    """Verify client classifies 401 and 403 as UPSTREAM_AUTH_FAILED."""
    for status_code in [401, 403]:
        transport = httpx.MockTransport(lambda req, sc=status_code: httpx.Response(sc))
        mock_http = httpx.AsyncClient(transport=transport)
        client = LinkedInClient(li_at="test", jsessionid="test", http_client=mock_http)

        with pytest.raises(ProfileForgeError) as exc_info:
            await client.fetch_profile_raw("sarah-jenkins")
        assert exc_info.value.error_code == ErrorCode.UPSTREAM_AUTH_FAILED
        assert exc_info.value.status_code == 502


@pytest.mark.asyncio
async def test_client_does_not_probe_another_endpoint_after_auth_failure():
    """Verify a rejected session fails once instead of replaying cookies elsewhere."""
    requested_paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested_paths.append(request.url.path)
        return httpx.Response(403)

    mock_http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    client = LinkedInClient(li_at="test", jsessionid="test", http_client=mock_http)

    with pytest.raises(ProfileForgeError) as exc_info:
        await client.fetch_profile_raw("sarah-jenkins")

    assert exc_info.value.error_code == ErrorCode.UPSTREAM_AUTH_FAILED
    assert requested_paths == ["/voyager/api/identity/dash/profiles"]


@pytest.mark.asyncio
async def test_client_handles_404_not_found():
    """Verify client classifies 404 as PROFILE_NOT_FOUND."""
    transport = httpx.MockTransport(lambda req: httpx.Response(404))
    mock_http = httpx.AsyncClient(transport=transport)
    client = LinkedInClient(li_at="test", jsessionid="test", http_client=mock_http)

    with pytest.raises(ProfileForgeError) as exc_info:
        await client.fetch_profile_raw("nonexistent-slug")
    assert exc_info.value.error_code == ErrorCode.PROFILE_NOT_FOUND
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_client_retries_transient_5xx_response(monkeypatch: pytest.MonkeyPatch):
    """Verify transient LinkedIn server failures receive bounded retries."""
    attempts = 0

    def handler(req: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(503)
        return httpx.Response(
            200, json={"included": [{"$type": "Profile", "firstName": "Sarah"}]}
        )

    async def no_sleep(delay: float) -> None:
        return None

    monkeypatch.setattr("app.providers.linkedin.client.asyncio.sleep", no_sleep)
    mock_http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    client = LinkedInClient(
        li_at="test", jsessionid="test", http_client=mock_http, max_retries=1
    )

    result = await client.fetch_profile_raw("sarah-jenkins")

    assert attempts == 2
    assert result["included"][0]["firstName"] == "Sarah"


@pytest.mark.asyncio
async def test_client_handles_999_and_429_rate_limits():
    """Verify client classifies HTTP 999 and 429 as UPSTREAM_RATE_LIMITED with Retry-After."""
    for code in [999, 429]:
        transport = httpx.MockTransport(
            lambda req, c=code: httpx.Response(c, headers={"Retry-After": "45"})
        )
        mock_http = httpx.AsyncClient(transport=transport)
        client = LinkedInClient(li_at="test", jsessionid="test", http_client=mock_http)

        with pytest.raises(ProfileForgeError) as exc_info:
            await client.fetch_profile_raw("sarah-jenkins")
        assert exc_info.value.error_code == ErrorCode.UPSTREAM_RATE_LIMITED
        assert exc_info.value.headers.get("Retry-After") == "45"


@pytest.mark.asyncio
async def test_client_detects_authwall_challenge_redirect():
    """Verify client classifies 302 redirects to authwall as UPSTREAM_CHALLENGE_DETECTED."""
    transport = httpx.MockTransport(
        lambda req: httpx.Response(
            302, headers={"Location": "https://www.linkedin.com/authwall?trk=..."}
        )
    )
    mock_http = httpx.AsyncClient(transport=transport)
    client = LinkedInClient(li_at="test", jsessionid="test", http_client=mock_http)

    with pytest.raises(ProfileForgeError) as exc_info:
        await client.fetch_profile_raw("sarah-jenkins")
    assert exc_info.value.error_code == ErrorCode.UPSTREAM_CHALLENGE_DETECTED
    assert exc_info.value.status_code == 502


@pytest.mark.asyncio
async def test_client_handles_malformed_json():
    """Verify client raises UPSTREAM_SCHEMA_CHANGED on non-JSON response body."""
    transport = httpx.MockTransport(
        lambda req: httpx.Response(200, text="<html><body>Not JSON</body></html>")
    )
    mock_http = httpx.AsyncClient(transport=transport)
    client = LinkedInClient(li_at="test", jsessionid="test", http_client=mock_http)

    with pytest.raises(ProfileForgeError) as exc_info:
        await client.fetch_profile_raw("sarah-jenkins")
    assert exc_info.value.error_code == ErrorCode.UPSTREAM_SCHEMA_CHANGED
    assert exc_info.value.status_code == 502
