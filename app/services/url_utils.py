"""URL validation, canonicalization, SSRF protection, and profile ID extraction."""

from __future__ import annotations

import ipaddress
import re
from urllib.parse import unquote, urlparse

from app.errors import ErrorCode, ProfileForgeError

# Allowed LinkedIn hostnames
ALLOWED_HOSTS = {
    "linkedin.com",
    "www.linkedin.com",
}

# Regex matching valid LinkedIn profile path: /in/<slug>
PROFILE_PATH_PATTERN = re.compile(r"^/in/([a-zA-Z0-9_\-\%]+)/?$", re.IGNORECASE)

BLOCKED_IP_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


def is_private_or_loopback(host: str) -> bool:
    """Check if host resolves to or directly specifies a private/loopback IP address."""
    clean_host = host.split(":")[0].strip("[]")
    try:
        ip = ipaddress.ip_address(clean_host)
        return any(ip in net for net in BLOCKED_IP_NETWORKS)
    except ValueError:
        return clean_host.lower() in {"localhost", "loopback", "127.0.0.1", "::1"}


def validate_and_canonicalize_url(raw_url: str) -> tuple[str, str]:
    """Validate user-provided profile URL, apply SSRF guards, and produce canonical representations.

    Args:
        raw_url: Untrusted input URL string.

    Returns:
        tuple of (canonical_url, canonical_profile_id)
        e.g. ("https://www.linkedin.com/in/sarah-jenkins-dev", "sarah-jenkins-dev")

    Raises:
        ProfileForgeError: If URL is invalid, non-LinkedIn, private/SSRF target, or lacks a valid profile slug.
    """
    if not raw_url or not isinstance(raw_url, str):
        raise ProfileForgeError(
            ErrorCode.INVALID_PROFILE_URL,
            "Profile URL must be a non-empty string.",
            status_code=400,
        )

    clean_url = raw_url.strip()
    # Add scheme if missing
    if not clean_url.startswith(("http://", "https://")):
        clean_url = "https://" + clean_url

    try:
        parsed = urlparse(clean_url)
    except Exception as exc:
        raise ProfileForgeError(
            ErrorCode.INVALID_PROFILE_URL,
            f"Malformed URL string: {clean_url}",
            status_code=400,
        ) from exc

    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https"}:
        raise ProfileForgeError(
            ErrorCode.INVALID_PROFILE_URL,
            f"Unsupported scheme '{scheme}'. Only HTTP and HTTPS are permitted.",
            status_code=400,
        )

    netloc = parsed.netloc.lower()
    if not netloc:
        raise ProfileForgeError(
            ErrorCode.INVALID_PROFILE_URL,
            "URL is missing a valid domain hostname.",
            status_code=400,
        )

    # SSRF guard against private IPs / localhosts
    if is_private_or_loopback(netloc):
        raise ProfileForgeError(
            ErrorCode.INVALID_PROFILE_URL,
            "Blocked destination: private or local loopback addresses are not permitted.",
            status_code=400,
        )

    # Strip port if present for hostname verification
    host_only = netloc.split(":")[0]

    # Hostname validation
    if host_only not in ALLOWED_HOSTS and not (
        host_only.endswith(".linkedin.com") and len(host_only.split(".")) == 3
    ):
        raise ProfileForgeError(
            ErrorCode.INVALID_PROFILE_URL,
            f"Invalid hostname '{host_only}'. Must be a valid LinkedIn profile domain (e.g. www.linkedin.com).",
            status_code=400,
        )

    path = parsed.path
    match = PROFILE_PATH_PATTERN.match(path)
    if not match:
        raise ProfileForgeError(
            ErrorCode.INVALID_PROFILE_URL,
            f"Invalid LinkedIn profile path '{path}'. Path must conform to '/in/<profile-identifier>'.",
            status_code=400,
        )

    raw_slug = match.group(1)
    slug = unquote(raw_slug).strip().lower()

    if not slug or len(slug) < 2:
        raise ProfileForgeError(
            ErrorCode.INVALID_PROFILE_URL,
            "Profile identifier in path is empty or too short.",
            status_code=400,
        )

    canonical_url = f"https://www.linkedin.com/in/{slug}"
    return canonical_url, slug
