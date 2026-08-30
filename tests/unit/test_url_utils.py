"""Unit tests for URL validation, canonicalization, and SSRF defenses."""

from __future__ import annotations

import pytest

from app.errors import ErrorCode, ProfileForgeError
from app.services.url_utils import validate_and_canonicalize_url


@pytest.mark.parametrize(
    "input_url, expected_canonical, expected_slug",
    [
        (
            "https://www.linkedin.com/in/sarah-jenkins-dev",
            "https://www.linkedin.com/in/sarah-jenkins-dev",
            "sarah-jenkins-dev",
        ),
        (
            "https://linkedin.com/in/sarah-jenkins-dev/",
            "https://www.linkedin.com/in/sarah-jenkins-dev",
            "sarah-jenkins-dev",
        ),
        (
            "http://www.linkedin.com/in/SARAH-JENKINS-DEV",
            "https://www.linkedin.com/in/sarah-jenkins-dev",
            "sarah-jenkins-dev",
        ),
        (
            "www.linkedin.com/in/williamhgates?trackingId=123#about",
            "https://www.linkedin.com/in/williamhgates",
            "williamhgates",
        ),
        (
            "https://uk.linkedin.com/in/john-doe-uk",
            "https://www.linkedin.com/in/john-doe-uk",
            "john-doe-uk",
        ),
    ],
)
def test_valid_linkedin_urls(
    input_url: str, expected_canonical: str, expected_slug: str
):
    canonical_url, slug = validate_and_canonicalize_url(input_url)
    assert canonical_url == expected_canonical
    assert slug == expected_slug


@pytest.mark.parametrize(
    "invalid_url",
    [
        "",
        "not-a-url",
        "ftp://www.linkedin.com/in/bad-scheme",
        "https://evil-phishing-linkedin.com/in/victim",
        "https://www.google.com/in/someone",
        "https://www.linkedin.com/company/techcorp",
        "https://www.linkedin.com/feed/",
        "https://www.linkedin.com/in/",
        "https://www.linkedin.com/in/a",  # too short
        "https://www.linkedin.com/in/jane%2Fdoe",  # encoded path separator
        "https://www.linkedin.com/in/jane%26role",  # encoded query delimiter
    ],
)
def test_invalid_linkedin_urls(invalid_url: str):
    with pytest.raises(ProfileForgeError) as exc_info:
        validate_and_canonicalize_url(invalid_url)
    assert exc_info.value.error_code == ErrorCode.INVALID_PROFILE_URL
    assert exc_info.value.status_code == 400


@pytest.mark.parametrize(
    "ssrf_target",
    [
        "http://127.0.0.1/in/admin",
        "http://localhost/in/admin",
        "http://10.0.0.1/in/root",
        "http://192.168.1.1/in/gateway",
        "http://169.254.169.254/in/metadata",
        "http://[::1]/in/loopback",
    ],
)
def test_ssrf_blocking(ssrf_target: str):
    with pytest.raises(ProfileForgeError) as exc_info:
        validate_and_canonicalize_url(ssrf_target)
    assert exc_info.value.error_code == ErrorCode.INVALID_PROFILE_URL
    assert exc_info.value.status_code == 400
    assert (
        "Blocked destination" in exc_info.value.message
        or "Invalid hostname" in exc_info.value.message
    )
