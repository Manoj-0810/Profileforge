"""Conditional live smoke test for verified upstream execution."""

from __future__ import annotations

import os

import pytest

from app.config import settings
from app.extractor.linkedin_direct import DirectLinkedInExtractor
from app.providers.linkedin.client import LinkedInClient


@pytest.mark.asyncio
async def test_live_linkedin_smoke_lookup():
    """Live smoke test executing a real direct HTTP profile lookup against LinkedIn.

    Skipped automatically in offline/CI environments unless live credentials are provided.
    """
    li_at = settings.LINKEDIN_LI_AT or os.getenv("LINKEDIN_LI_AT")
    jsessionid = settings.LINKEDIN_JSESSIONID or os.getenv("LINKEDIN_JSESSIONID")
    target_url = os.getenv(
        "LIVE_TEST_PROFILE_URL", "https://www.linkedin.com/in/williamhgates"
    )

    if not li_at or not jsessionid:
        pytest.skip(
            "Live smoke test skipped: Set LINKEDIN_LI_AT and LINKEDIN_JSESSIONID to run."
        )

    client = LinkedInClient(
        li_at=li_at,
        jsessionid=jsessionid,
        user_agent=settings.LINKEDIN_USER_AGENT,
        proxy_url=settings.LINKEDIN_PROXY_URL,
        timeout_seconds=settings.UPSTREAM_TIMEOUT_SECONDS,
    )
    extractor = DirectLinkedInExtractor(client=client)

    try:
        profile = await extractor.fetch(target_url)
        assert profile.full_name, "Live parsed profile must have a valid non-empty name"
        assert profile.canonical_url.startswith("https://www.linkedin.com/in/")
    finally:
        await client.close()
