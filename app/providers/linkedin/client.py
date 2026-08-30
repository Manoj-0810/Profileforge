"""Direct HTTP client for reverse-engineered LinkedIn Rest.li Voyager API."""

from __future__ import annotations

import asyncio
import random
from typing import Any

import httpx
import structlog

from app.errors import ErrorCode, ProfileForgeError

logger = structlog.get_logger(__name__)

VOYAGER_BASE_URL = "https://www.linkedin.com/voyager/api"
DASH_PROFILE_ENDPOINT = f"{VOYAGER_BASE_URL}/identity/dash/profiles"
DEFAULT_DECORATION_ID = (
    "com.linkedin.voyager.dash.deco.identity.profile.FullProfileWithEntities-93"
)
PROFILE_DECORATION_ID = DEFAULT_DECORATION_ID


class LinkedInRequestBuilder:
    """Constructs authenticated HTTP requests for LinkedIn Voyager endpoints."""

    @staticmethod
    def build_profile_url(slug: str) -> str:
        """Construct the primary Voyager Dash profile endpoint URL."""
        return f"{DASH_PROFILE_ENDPOINT}?q=memberIdentity&memberIdentity={slug}&decorationId={DEFAULT_DECORATION_ID}"

    @staticmethod
    def build_legacy_profile_url(slug: str) -> str:
        """Construct the legacy Voyager profileView endpoint URL."""
        return f"{VOYAGER_BASE_URL}/identity/profiles/{slug}/profileView"

    @staticmethod
    def derive_csrf_token(jsessionid: str) -> str:
        """Derive the required csrf-token header from JSESSIONID by stripping quotes."""
        return jsessionid.strip().strip('"').strip("'")

    @classmethod
    def build_headers(
        cls,
        jsessionid: str,
        user_agent: str,
    ) -> dict[str, str]:
        """Construct standard browser-like Rest.li request headers."""
        csrf_token = cls.derive_csrf_token(jsessionid)
        return {
            "csrf-token": csrf_token,
            "x-restli-protocol-version": "2.0.0",
            "accept": "application/vnd.linkedin.normalized+json+2.1",
            "x-li-lang": "en_US",
            "x-li-track": "{}",
            "x-li-page-instance": "urn:li:page:d_flagship3_profile_view_base;null",
            "user-agent": user_agent,
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
        }

    @staticmethod
    def build_cookies(li_at: str, jsessionid: str) -> dict[str, str]:
        """Build session cookie mapping for authentication."""
        return {
            "li_at": li_at.strip().strip('"').strip("'"),
            "JSESSIONID": jsessionid.strip(),
        }


class LinkedInClient:
    """HTTP client executing direct reverse-engineered calls to LinkedIn Rest.li Voyager endpoints."""

    def __init__(
        self,
        li_at: str,
        jsessionid: str,
        user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        proxy_url: str | None = None,
        timeout_seconds: float = 30.0,
        max_retries: int = 2,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.li_at = li_at.strip()
        self.jsessionid = jsessionid.strip()
        self.user_agent = user_agent.strip()
        self.proxy_url = proxy_url.strip() if proxy_url else None
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self._external_client = http_client
        self._internal_client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        """Get or initialize the persistent AsyncClient."""
        if self._external_client is not None:
            return self._external_client
        if self._internal_client is None or self._internal_client.is_closed:
            timeout_config = httpx.Timeout(
                connect=10.0,
                read=self.timeout_seconds,
                write=10.0,
                pool=10.0,
            )
            self._internal_client = httpx.AsyncClient(
                timeout=timeout_config,
                proxy=self.proxy_url,
                follow_redirects=True,
            )
        return self._internal_client

    async def close(self) -> None:
        """Close the internal HTTP client connection pool if allocated."""
        if self._internal_client is not None and not self._internal_client.is_closed:
            await self._internal_client.aclose()
            self._internal_client = None

    async def fetch_profile_raw(self, slug: str) -> dict[str, Any]:
        """Execute direct HTTP request to fetch profile data for a member slug.

        Args:
            slug: Clean public LinkedIn member identifier (e.g. 'sarah-jenkins-dev').

        Returns:
            Parsed JSON dictionary containing the normalized entity graph.

        Raises:
            ProfileForgeError: Standardized error code mapping on upstream failure.
        """
        if not self.li_at or not self.jsessionid:
            raise ProfileForgeError(
                ErrorCode.AUTH_CONFIGURATION_ERROR,
                "LinkedIn session credentials (LINKEDIN_LI_AT and LINKEDIN_JSESSIONID) are missing.",
                status_code=503,
            )

        headers = LinkedInRequestBuilder.build_headers(self.jsessionid, self.user_agent)
        cookies = LinkedInRequestBuilder.build_cookies(self.li_at, self.jsessionid)
        client = self._get_client()

        # Try Dash endpoint first, then legacy profileView endpoint if necessary
        endpoints_to_try = [
            LinkedInRequestBuilder.build_profile_url(slug),
            LinkedInRequestBuilder.build_legacy_profile_url(slug),
        ]

        last_error: Exception | None = None

        for endpoint_idx, target_url in enumerate(endpoints_to_try):
            attempt = 0
            while True:
                attempt += 1
                try:
                    logger.info(
                        "upstream_linkedin_fetch_start",
                        slug=slug,
                        endpoint_index=endpoint_idx,
                        attempt=attempt,
                        url=target_url,
                    )
                    response = await client.get(
                        target_url,
                        headers=headers,
                        cookies=cookies,
                    )

                    # If 5xx, retry with exponential backoff
                    if (
                        500 <= response.status_code < 600
                        and attempt <= self.max_retries
                    ):
                        backoff = (2 ** (attempt - 1)) + random.uniform(0.1, 0.5)
                        logger.warning(
                            "upstream_linkedin_server_retry",
                            slug=slug,
                            attempt=attempt,
                            status=response.status_code,
                            backoff_seconds=round(backoff, 2),
                        )
                        await asyncio.sleep(backoff)
                        continue

                    # If primary endpoint returned 403/404 and fallback is available, try fallback
                    if response.status_code in (403, 404) and endpoint_idx == 0:
                        logger.warning(
                            "upstream_primary_endpoint_failed_trying_fallback",
                            slug=slug,
                            status=response.status_code,
                        )
                        break

                    return self._classify_and_handle_response(response, slug)

                except httpx.TimeoutException as exc:
                    logger.warning(
                        "upstream_linkedin_timeout",
                        slug=slug,
                        attempt=attempt,
                        error=str(exc),
                    )
                    if attempt <= self.max_retries:
                        backoff = (2 ** (attempt - 1)) + random.uniform(0.1, 0.5)
                        await asyncio.sleep(backoff)
                        continue
                    last_error = ProfileForgeError(
                        ErrorCode.UPSTREAM_TIMEOUT,
                        f"LinkedIn upstream timed out after {self.timeout_seconds}s.",
                        status_code=504,
                    )
                    break

                except httpx.NetworkError as exc:
                    logger.warning(
                        "upstream_linkedin_network_error",
                        slug=slug,
                        attempt=attempt,
                        error=str(exc),
                    )
                    if attempt <= self.max_retries:
                        backoff = (2 ** (attempt - 1)) + random.uniform(0.1, 0.5)
                        await asyncio.sleep(backoff)
                        continue
                    last_error = ProfileForgeError(
                        ErrorCode.UPSTREAM_UNAVAILABLE,
                        f"Network error connecting to LinkedIn upstream: {exc}",
                        status_code=502,
                    )
                    break

                except ProfileForgeError as exc:
                    last_error = exc
                    break

                except Exception as exc:
                    logger.exception(
                        "upstream_linkedin_unexpected_error",
                        slug=slug,
                        attempt=attempt,
                        error=str(exc),
                    )
                    last_error = ProfileForgeError(
                        ErrorCode.UPSTREAM_SERVER_ERROR,
                        f"Unexpected error communicating with LinkedIn: {exc}",
                        status_code=502,
                    )
                    break

        if last_error is not None:
            raise last_error

        raise ProfileForgeError(
            ErrorCode.UPSTREAM_SERVER_ERROR,
            "Failed to retrieve profile from all upstream endpoints.",
            status_code=502,
        )

    def _classify_and_handle_response(
        self, response: httpx.Response, slug: str
    ) -> dict[str, Any]:
        """Classify HTTP response status code and body into domain errors or raw JSON data."""
        status_code = response.status_code

        # 1. Challenge & Redirect Detection (Checking final URL and history)
        final_url = str(response.url).lower()
        redirect_target = response.headers.get("Location", "")

        is_authwall = any(
            p in final_url or p in redirect_target.lower()
            for p in ["authwall", "checkpoint", "login", "challenge", "uas/login"]
        )

        if is_authwall:
            logger.warning(
                "upstream_challenge_detected",
                slug=slug,
                status=status_code,
                final_url=final_url,
                location=redirect_target,
            )
            raise ProfileForgeError(
                ErrorCode.UPSTREAM_CHALLENGE_DETECTED,
                "LinkedIn presented an authentication challenge / authwall. "
                "Session cookies (li_at, JSESSIONID) may be expired, flagged, or invalid.",
                status_code=502,
            )

        if status_code in (301, 302, 303, 307, 308):
            logger.warning(
                "upstream_redirect",
                slug=slug,
                status=status_code,
                location=redirect_target,
            )
            if not redirect_target:
                raise ProfileForgeError(
                    ErrorCode.UPSTREAM_SERVER_ERROR,
                    f"Unexpected redirect from LinkedIn with status {status_code}.",
                    status_code=502,
                )

        # 2. HTTP 999 (LinkedIn Bot Challenge) & HTTP 429 (Rate Limit)
        if status_code in (999, 429):
            retry_after = response.headers.get("Retry-After", "60")
            logger.warning(
                "upstream_rate_limited",
                slug=slug,
                status=status_code,
                retry_after=retry_after,
            )
            raise ProfileForgeError(
                ErrorCode.UPSTREAM_RATE_LIMITED,
                f"LinkedIn rate limit reached (HTTP {status_code}). Retry after {retry_after}s.",
                status_code=502,
                headers={"Retry-After": retry_after},
            )

        # 3. Authentication Failures
        if status_code == 401:
            logger.warning("upstream_auth_unauthorized", slug=slug)
            raise ProfileForgeError(
                ErrorCode.UPSTREAM_AUTH_FAILED,
                "LinkedIn session cookie (li_at) is expired or invalid.",
                status_code=502,
            )

        if status_code == 403:
            logger.warning("upstream_auth_forbidden", slug=slug)
            raise ProfileForgeError(
                ErrorCode.UPSTREAM_AUTH_FAILED,
                "LinkedIn access forbidden (403). Please verify that your li_at session cookie and JSESSIONID are fresh and copied from an active LinkedIn browser session.",
                status_code=502,
            )

        # 4. Profile Not Found
        if status_code == 404:
            logger.info("upstream_profile_not_found", slug=slug)
            raise ProfileForgeError(
                ErrorCode.PROFILE_NOT_FOUND,
                f"LinkedIn profile '{slug}' was not found.",
                status_code=404,
            )

        # 5. Upstream Server Errors
        if status_code >= 500:
            logger.error("upstream_server_error", slug=slug, status=status_code)
            raise ProfileForgeError(
                ErrorCode.UPSTREAM_SERVER_ERROR,
                f"LinkedIn upstream returned server error (HTTP {status_code}).",
                status_code=502,
            )

        # 6. Parse 200 OK Body
        if status_code == 200:
            # Check if LinkedIn returned HTML login/challenge page instead of JSON
            content_type = response.headers.get("content-type", "").lower()
            if "text/html" in content_type:
                logger.warning("upstream_html_response_detected", slug=slug)
                raise ProfileForgeError(
                    ErrorCode.UPSTREAM_CHALLENGE_DETECTED,
                    "LinkedIn returned an HTML challenge/login page instead of JSON data. "
                    "Session credentials (li_at) may be expired or require fresh login.",
                    status_code=502,
                )

            try:
                data = response.json()
                if not isinstance(data, dict):
                    raise TypeError("Root JSON payload must be an object")
                return data
            except Exception as exc:
                logger.error(
                    "upstream_json_parse_failed",
                    slug=slug,
                    error=str(exc),
                    content_type=response.headers.get("content-type", ""),
                )
                raise ProfileForgeError(
                    ErrorCode.UPSTREAM_SCHEMA_CHANGED,
                    "LinkedIn returned malformed or non-JSON body.",
                    status_code=502,
                ) from exc

        # 7. Unhandled Status Code
        logger.error("upstream_unhandled_status", slug=slug, status=status_code)
        raise ProfileForgeError(
            ErrorCode.UPSTREAM_SERVER_ERROR,
            f"LinkedIn returned unexpected HTTP status code {status_code}.",
            status_code=502,
        )
