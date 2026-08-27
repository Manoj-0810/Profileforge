"""Base extractor protocol defining the provider interface."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.models import ProfileData, ProviderCapabilities


@runtime_checkable
class ProfileExtractor(Protocol):
    """Protocol that all profile extraction providers must satisfy."""

    @property
    def capabilities(self) -> ProviderCapabilities:
        """Return the capabilities profile of this extractor."""
        ...

    async def fetch(self, canonical_url: str) -> ProfileData:
        """Fetch and normalize profile data for a canonical LinkedIn profile URL.

        Args:
            canonical_url: Normalized LinkedIn profile URL.

        Returns:
            Normalized ProfileData instance.

        Raises:
            ProfileForgeError: If extraction fails, times out, or receives an error.
        """
        ...
