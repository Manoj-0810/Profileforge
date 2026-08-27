"""Conditional live smoke test for verified upstream execution."""

from __future__ import annotations

import os

import pytest

from app.config import settings
from app.providers.linkedapi.client import LinkedAPIClient
from app.providers.linkedapi.normalizer import LinkedAPINormalizer
from app.providers.linkedapi.parser import LinkedAPIParser


@pytest.mark.asyncio
async def test_live_linkedapi_smoke_lookup():
    """Live smoke test executing a real profile lookup against api.linkedapi.io.

    Skipped automatically in offline/CI environments unless live credentials are provided.
    """
    token = settings.LINKEDAPI_TOKEN or os.getenv("LINKEDAPI_TOKEN")
    ident = settings.LINKEDAPI_IDENTIFICATION_TOKEN or os.getenv(
        "LINKEDAPI_IDENTIFICATION_TOKEN"
    )
    target_url = os.getenv(
        "LIVE_TEST_PROFILE_URL", "https://www.linkedin.com/in/williamhgates"
    )

    if not token or not ident:
        pytest.skip(
            "Live smoke test skipped: Set LINKEDAPI_TOKEN and LINKEDAPI_IDENTIFICATION_TOKEN to run."
        )

    client = LinkedAPIClient(
        api_token=token,
        identification_token=ident,
        timeout_seconds=120.0,
        poll_interval_seconds=3.0,
    )
    parser = LinkedAPIParser()
    normalizer = LinkedAPINormalizer()

    completion = await client.execute_profile_workflow(target_url)
    assert completion.get("success") is True

    parsed = parser.parse(completion)
    assert parsed.name, "Live parsed profile must have a valid non-empty name"

    profile = normalizer.normalize(parsed, target_url)
    assert profile.full_name == parsed.name
    assert profile.canonical_url.startswith("https://www.linkedin.com/in/")
