"""Mock extractor implementation for deterministic offline testing and local development."""

from __future__ import annotations

from app.errors import ErrorCode, ProfileForgeError
from app.extractor.base import ProfileExtractor
from app.models import (
    CertificationEntry,
    EducationEntry,
    ExperienceEntry,
    LanguageEntry,
    ProfileData,
    ProviderCapabilities,
)

MOCK_CAPABILITIES = ProviderCapabilities(
    provider_name="mock",
    supported_sections={
        "full_name",
        "headline",
        "location",
        "about",
        "experience",
        "education",
        "skills",
        "certifications",
        "languages",
        "profile_image_url",
    },
    unsupported_sections=set(),
    supports_realtime_polling=False,
    max_recommended_concurrency=10,
)


class MockExtractor(ProfileExtractor):
    """Deterministic, offline extractor returning rich fixture-backed profiles."""

    def __init__(self, capabilities: ProviderCapabilities | None = None) -> None:
        self._capabilities = capabilities or MOCK_CAPABILITIES

    @property
    def capabilities(self) -> ProviderCapabilities:
        return self._capabilities

    async def fetch(self, canonical_url: str) -> ProfileData:
        """Return deterministic ProfileData based on slug in canonical_url."""
        slug = canonical_url.rstrip("/").split("/")[-1].lower()

        # Simulated Error Conditions
        if "not-found" in slug or "nonexistent" in slug:
            raise ProfileForgeError(
                ErrorCode.PROFILE_NOT_FOUND,
                f"Profile '{slug}' not found on LinkedIn",
                status_code=404,
            )

        if "auth-fail" in slug:
            raise ProfileForgeError(
                ErrorCode.UPSTREAM_AUTH_FAILED,
                "LinkedIn session cookie expired or invalid",
                status_code=502,
            )

        if "rate-limit" in slug:
            raise ProfileForgeError(
                ErrorCode.UPSTREAM_RATE_LIMITED,
                "Upstream rate limit exceeded for account",
                status_code=502,
                headers={"Retry-After": "60"},
            )

        if "challenge" in slug:
            raise ProfileForgeError(
                ErrorCode.UPSTREAM_CHALLENGE_DETECTED,
                "LinkedIn presented an authentication challenge / authwall redirect",
                status_code=502,
            )

        if "timeout" in slug:
            raise ProfileForgeError(
                ErrorCode.UPSTREAM_TIMEOUT,
                "Upstream profile lookup timed out after 30.0s",
                status_code=504,
            )

        if "schema-drift" in slug:
            raise ProfileForgeError(
                ErrorCode.UPSTREAM_SCHEMA_CHANGED,
                "Upstream schema structurally altered",
                status_code=502,
            )

        # Profile Variations
        if "alex-mercer" in slug or "partial" in slug:
            return ProfileData(
                full_name="Alex Mercer",
                headline="Backend Engineer | Python & Go",
                location="Austin, Texas, United States",
                country_code="US",
                about=None,
                profile_image_url="https://media.licdn.com/dms/image/v2/alex-mercer.jpg",
                profile_url=canonical_url,
                canonical_url=canonical_url,
                urn="urn:li:fsd_profile:ACoAAALEXMERCER",
                current_position="Backend Engineer",
                current_company="Nexus Systems",
                followers_count=420,
                experience=[
                    ExperienceEntry(
                        title="Backend Engineer",
                        company="Nexus Systems",
                        company_url="https://www.linkedin.com/company/nexus-systems",
                        location_type="Remote",
                        start_date="2022-03",
                        end_date=None,
                    )
                ],
                education=[
                    EducationEntry(
                        school="University of Texas at Austin",
                        degree="Bachelor of Science",
                        field_of_study="Computer Science",
                        start_date="2018",
                        end_date="2022",
                    )
                ],
                skills=["Python", "FastAPI", "Go", "Docker", "PostgreSQL"],
                certifications=[],
                languages=[
                    LanguageEntry(name="English", proficiency="Native or bilingual")
                ],
            )

        if "minimal" in slug or "maya-lin" in slug:
            return ProfileData(
                full_name="Maya Lin",
                headline="AI Research Scientist",
                location="Seattle, Washington, United States",
                country_code="US",
                about=None,
                profile_image_url=None,
                profile_url=canonical_url,
                canonical_url=canonical_url,
                urn="urn:li:fsd_profile:ACoAAAMAYALIN",
                current_position=None,
                current_company=None,
                followers_count=1250,
                experience=[],
                education=[],
                skills=["PyTorch", "Deep Learning", "Transformers"],
                certifications=[],
                languages=[],
            )

        # Default Complete Profile (Sarah Jenkins)
        return ProfileData(
            full_name="Sarah Jenkins",
            headline="Staff Software Engineer | Distributed Systems & Cloud Architecture",
            location="San Francisco, California, United States",
            country_code="US",
            about="Staff Engineer with 10+ years specializing in high-throughput distributed systems, microservices architecture, and cloud platforms.",
            profile_image_url="https://media.licdn.com/dms/image/v2/sarah-jenkins-avatar.jpg",
            profile_url=canonical_url,
            canonical_url=canonical_url,
            urn="urn:li:fsd_profile:ACoAAASARAHJENKINS",
            current_position="Staff Software Engineer",
            current_company="Stripe",
            followers_count=4850,
            experience=[
                ExperienceEntry(
                    title="Staff Software Engineer",
                    company="Stripe",
                    company_url="https://www.linkedin.com/company/stripe",
                    employment_type="Full-time",
                    location_type="Hybrid",
                    location="San Francisco, CA",
                    description="Leading core payments ingestion pipeline architecture handling 50k+ QPS with 99.999% availability.",
                    start_date="2021-04",
                    end_date=None,
                ),
                ExperienceEntry(
                    title="Senior Software Engineer",
                    company="Uber",
                    company_url="https://www.linkedin.com/company/uber",
                    employment_type="Full-time",
                    location_type="On-site",
                    location="San Francisco, CA",
                    description="Built distributed tracing and RPC routing infrastructure in Go and gRPC.",
                    start_date="2018-06",
                    end_date="2021-03",
                ),
            ],
            education=[
                EducationEntry(
                    school="Stanford University",
                    degree="Master of Science",
                    field_of_study="Computer Science",
                    start_date="2016",
                    end_date="2018",
                ),
                EducationEntry(
                    school="University of California, Berkeley",
                    degree="Bachelor of Science",
                    field_of_study="Electrical Engineering & Computer Science",
                    start_date="2012",
                    end_date="2016",
                ),
            ],
            skills=[
                "Distributed Systems",
                "Python",
                "FastAPI",
                "Go",
                "Kubernetes",
                "PostgreSQL",
                "Redis",
                "System Design",
            ],
            certifications=[
                CertificationEntry(
                    name="AWS Certified Solutions Architect - Professional",
                    issuing_organization="Amazon Web Services",
                    issue_date="2022-05",
                    expiration_date="2025-05",
                    credential_id="AWS-PSA-99482",
                )
            ],
            languages=[
                LanguageEntry(name="English", proficiency="Native or bilingual"),
                LanguageEntry(name="French", proficiency="Professional working"),
            ],
        )
