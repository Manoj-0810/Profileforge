"""Direct HTTP client for reverse-engineered LinkedIn Voyager endpoints."""

from __future__ import annotations

import asyncio
import random
from typing import Any

import httpx
import structlog

from app.errors import ErrorCode, ProfileForgeError

logger = structlog.get_logger(__name__)

VOYAGER_BASE_URL = "https://www.linkedin.com/voyager/api"
DEFAULT_DECORATION_ID = (
    "com.linkedin.voyager.dash.deco.identity.profile.FullProfileWithEntities-93"
)


class LinkedInRequestBuilder:
    """Explicit request builder for LinkedIn Voyager API interactions."""

    @staticmethod
    def build_profile_url(slug: str, decoration_id: str = DEFAULT_DECORATION_ID) -> str:
        """Construct the full parameterized Voyager Dash profiles URL."""
        params = httpx.QueryParams(
            {
                "q": "memberIdentity",
                "memberIdentity": slug,
                "decorationId": decoration_id,
            }
        )
        return f"{VOYAGER_BASE_URL}/identity/dash/profiles?{params}"

    @staticmethod
    def build_legacy_profile_url(slug: str) -> str:
        """Construct the fallback / legacy Voyager profileView URL."""
        return f"{VOYAGER_BASE_URL}/identity/profiles/{slug}/profileView"

    @staticmethod
    def build_headers(jsessionid: str, user_agent: str) -> dict[str, str]:
        """Construct required HTTP headers with derived CSRF token."""
        csrf_token = jsessionid.strip('"')
        return {
            "csrf-token": csrf_token,
            "x-restli-protocol-version": "2.0.0",
            "accept": "application/vnd.linkedin.normalized+json+2.1",
            "x-li-lang": "en_US",
            "user-agent": user_agent,
        }

    @staticmethod
    def build_cookies(li_at: str, jsessionid: str) -> dict[str, str]:
        """Construct cookie dictionary for session authentication."""
        return {
            "li_at": li_at,
            "JSESSIONID": jsessionid,
        }


class LinkedInClient:
    """Direct HTTP client executing browserless requests against LinkedIn endpoints."""

    def __init__(
        self,
        li_at: str = "",
        jsessionid: str = "",
        user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        proxy_url: str | None = None,
        timeout_seconds: float = 30.0,
        max_retries: int = 2,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.li_at = li_at
        self.jsessionid = jsessionid
        self.user_agent = user_agent
        self.proxy_url = proxy_url
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
                connect=5.0,
                read=self.timeout_seconds,
                write=5.0,
                pool=5.0,
            )
            self._internal_client = httpx.AsyncClient(
                timeout=timeout_config,
                proxy=self.proxy_url,
                follow_redirects=False,
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
            logger.error("linkedin_credentials_missing", slug=slug)
            raise ProfileForgeError(
                ErrorCode.AUTH_CONFIGURATION_ERROR,
                "LinkedIn session credentials (LINKEDIN_LI_AT and "
                "LINKEDIN_JSESSIONID) are not configured. "
                "Please configure LINKEDIN_LI_AT and LINKEDIN_JSESSIONID in server environment variables.",
                status_code=503,
            )

        target_url = LinkedInRequestBuilder.build_profile_url(slug)
        headers = LinkedInRequestBuilder.build_headers(self.jsessionid, self.user_agent)
        cookies = LinkedInRequestBuilder.build_cookies(self.li_at, self.jsessionid)

        client = self._get_client()
        attempt = 0

        while True:
            attempt += 1
            try:
                logger.info(
                    "upstream_linkedin_fetch_start",
                    slug=slug,
                    attempt=attempt,
                    url=target_url,
                )
                response = await client.get(
                    target_url,
                    headers=headers,
                    cookies=cookies,
                )
                if 500 <= response.status_code < 600 and attempt <= self.max_retries:
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
                raise ProfileForgeError(
                    ErrorCode.UPSTREAM_TIMEOUT,
                    f"LinkedIn upstream timed out after {self.timeout_seconds}s.",
                    status_code=504,
                ) from exc

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
                raise ProfileForgeError(
                    ErrorCode.UPSTREAM_UNAVAILABLE,
                    f"Network error connecting to LinkedIn upstream: {exc}",
                    status_code=502,
                ) from exc

            except ProfileForgeError:
                raise

            except Exception as exc:
                logger.exception(
                    "upstream_linkedin_unexpected_error",
                    slug=slug,
                    attempt=attempt,
                    error=str(exc),
                )
                raise ProfileForgeError(
                    ErrorCode.UPSTREAM_SERVER_ERROR,
                    f"Unexpected error communicating with LinkedIn: {exc}",
                    status_code=502,
                ) from exc

    def _classify_and_handle_response(
        self, response: httpx.Response, slug: str
    ) -> dict[str, Any]:
        """Classify HTTP response status code and body into domain errors or raw JSON data."""
        status_code = response.status_code

        # 1. Challenge & Redirect Detection
        if status_code in (301, 302, 303, 307, 308):
            redirect_target = response.headers.get("Location", "")
            logger.warning(
                "upstream_challenge_redirect",
                slug=slug,
                status=status_code,
                location=redirect_target,
            )
            if any(
                p in redirect_target.lower()
                for p in ["authwall", "checkpoint", "login", "challenge"]
            ):
                raise ProfileForgeError(
                    ErrorCode.UPSTREAM_CHALLENGE_DETECTED,
                    "LinkedIn presented an authentication challenge / authwall redirect. "
                    "Session credentials may require manual renewal before retrying.",
                    status_code=502,
                )
            raise ProfileForgeError(
                ErrorCode.UPSTREAM_SERVER_ERROR,
                f"Unexpected redirect from LinkedIn: {redirect_target}",
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
                f"LinkedIn rate limited or challenged the session (HTTP {status_code}).",
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
                "LinkedIn access forbidden. Verify session permissions and CSRF token.",
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

        # 6. Parse 200 OK JSON Body
        if status_code == 200:
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
            f"Unexpected response status from LinkedIn: {status_code}",
            status_code=502,
        )
