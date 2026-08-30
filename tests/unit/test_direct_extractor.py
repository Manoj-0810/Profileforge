"""Unit tests for DirectLinkedInExtractor adapter."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from app.extractor.linkedin_direct import DirectLinkedInExtractor
from app.models import ProfileData
from app.providers.linkedin.client import LinkedInClient
from app.providers.linkedin.normalizer import LinkedInNormalizer
from app.providers.linkedin.parser import LinkedInParser
from app.providers.linkedin.resolver import LinkedInResolver

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "raw_upstream"


@pytest.mark.asyncio
async def test_direct_extractor_fetch():
    """Verify DirectLinkedInExtractor fetches and normalizes data through the pipeline."""
    sample_response = {
        "included": [
            {
                "$type": "com.linkedin.voyager.dash.identity.profile.Profile",
                "entityUrn": "urn:li:fsd_profile:ACoAAATEST",
                "firstName": "Jane",
                "lastName": "Developer",
                "headline": "Senior Software Engineer",
                "locationName": "New York, NY",
            },
            {
                "$type": "com.linkedin.voyager.dash.identity.profile.Position",
                "title": "Senior Software Engineer",
                "companyName": "TechCorp",
            },
            {
                "$type": "com.linkedin.voyager.dash.identity.profile.Skill",
                "name": "Python",
            },
        ]
    }

    transport = httpx.MockTransport(
        lambda req: httpx.Response(200, json=sample_response)
    )
    mock_http = httpx.AsyncClient(transport=transport)
    client = LinkedInClient(
        li_at="test-token", jsessionid="ajax:123", http_client=mock_http
    )
    extractor = DirectLinkedInExtractor(client=client)

    assert extractor.capabilities.provider_name == "linkedin_direct"

    profile = await extractor.fetch("https://www.linkedin.com/in/jane-developer")
    assert isinstance(profile, ProfileData)
    assert profile.full_name == "Jane Developer"
    assert profile.headline == "Senior Software Engineer"
    assert len(profile.experience) == 1
    assert profile.experience[0].title == "Senior Software Engineer"
    assert "Python" in profile.skills


@pytest.mark.asyncio
async def test_direct_extractor_complete_voyager_fixture():
    """Verify DirectLinkedInExtractor against full voyager_complete.json fixture."""
    fixture_path = FIXTURES_DIR / "voyager_complete.json"
    voyager_payload = json.loads(fixture_path.read_text(encoding="utf-8"))

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "www.linkedin.com"
        assert request.url.path == "/voyager/api/identity/dash/profiles"
        assert request.url.params["memberIdentity"] == "sarah-jenkins-dev"
        assert request.headers.get("csrf-token") == "ajax:123"
        assert "li_at=test-li-at" in request.headers.get("cookie", "")
        return httpx.Response(200, json=voyager_payload)

    mock_http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    client = LinkedInClient(
        li_at="test-li-at",
        jsessionid="ajax:123",
        http_client=mock_http,
    )
    extractor = DirectLinkedInExtractor(client=client)

    profile = await extractor.fetch("https://www.linkedin.com/in/sarah-jenkins-dev")
    assert isinstance(profile, ProfileData)
    assert profile.full_name == "Sarah Jenkins"
    assert (
        profile.headline
        == "Staff Software Engineer | Distributed Systems & Cloud Architecture"
    )
    assert profile.location == "San Francisco, California, United States"
    assert profile.about is not None
    assert len(profile.experience) == 2
    assert profile.experience[0].company == "Stripe"
    assert len(profile.education) == 2
    assert profile.education[0].school == "Stanford University"
    assert "Distributed Systems" in profile.skills
    assert len(profile.certifications) >= 1
    assert len(profile.languages) >= 1
    assert (
        profile.profile_image_url
        == "https://media.licdn.com/dms/image/v2/sarah-jenkins-800.jpg"
    )

    # Verify normalization output
    parsed = LinkedInParser.parse(voyager_payload)
    resolved = LinkedInResolver.resolve(parsed)
    _norm_profile, dq = LinkedInNormalizer.normalize(
        resolved, canonical_url="https://www.linkedin.com/in/sarah-jenkins-dev"
    )
    assert dq.completeness_score >= 0.8
