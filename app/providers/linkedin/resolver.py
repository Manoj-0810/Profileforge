"""Entity reference resolution and field parsing for LinkedIn Voyager data."""

from __future__ import annotations

import re
from typing import Any

import structlog
from pydantic import BaseModel, ConfigDict, Field

from app.models import (
    CertificationEntry,
    EducationEntry,
    ExperienceEntry,
    LanguageEntry,
)
from app.providers.linkedin.parser import ParsedVoyagerData

logger = structlog.get_logger(__name__)

DEGREE_PATTERNS = [
    r"\bBachelor(?:'s)?(?:\s+of\s+[A-Za-z\s]+)?\b",
    r"\bMaster(?:'s)?(?:\s+of\s+[A-Za-z\s]+)?\b",
    r"\bDoctor(?:ate)?(?:\s+of\s+[A-Za-z\s]+)?\b",
    r"\bExecutive MBA\b",
    r"\bMBA\b",
    r"\bPh\.?D\.?",
    r"\bB\.?S\.?(?:c\.?)?",
    r"\bM\.?S\.?(?:c\.?)?",
    r"\bB\.?A\.?",
    r"\bM\.?A\.?",
    r"\bB\.?E\.?",
    r"\bM\.?E\.?",
    r"\bB\.?Tech\.?",
    r"\bM\.?Tech\.?",
    r"\bAssociate(?:'s)?(?:\s+of\s+[A-Za-z\s]+)?\b",
    r"\bDiploma\b",
    r"\bCertificate\b",
]


class ResolvedProfileRecords(BaseModel):
    """Container holding fully resolved domain entries and profile metadata."""

    model_config = ConfigDict(extra="ignore")

    full_name: str = ""
    headline: str | None = None
    location: str | None = None
    country_code: str | None = None
    about: str | None = None
    profile_image_url: str | None = None
    urn: str | None = None
    current_position: str | None = None
    current_company: str | None = None
    followers_count: int | None = None
    experience: list[ExperienceEntry] = Field(default_factory=list)
    education: list[EducationEntry] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    certifications: list[CertificationEntry] = Field(default_factory=list)
    languages: list[LanguageEntry] = Field(default_factory=list)


class LinkedInResolver:
    """Resolves foreign entity references, URN indices, and field normalizations."""

    @classmethod
    def resolve(cls, parsed: ParsedVoyagerData) -> ResolvedProfileRecords:
        """Resolve entity graph and construct typed entries."""
        # 1. Build index by entityUrn and objectUrn for fast dereferencing
        urn_index: dict[str, dict[str, Any]] = {}
        for entity in parsed.raw_entities:
            for urn_key in [
                "entityUrn",
                "objectUrn",
                "*profile",
                "*company",
                "*school",
            ]:
                if urn_key in entity and isinstance(entity[urn_key], str):
                    urn_index[entity[urn_key]] = entity

        # 2. Resolve Base Profile Information
        prof = parsed.profile_entity
        first_name = prof.get("firstName", "").strip()
        last_name = prof.get("lastName", "").strip()

        if first_name and last_name:
            full_name = f"{first_name} {last_name}".strip()
        elif first_name:
            full_name = first_name
        elif "name" in prof:
            full_name = str(prof["name"]).strip()
        elif "fullName" in prof:
            full_name = str(prof["fullName"]).strip()
        else:
            full_name = "N/A"

        headline = prof.get("headline") or prof.get("title") or None
        if headline:
            headline = str(headline).strip() or None

        raw_location = (
            prof.get("locationName")
            or prof.get("geoCountryName")
            or prof.get("location")
            or prof.get("geoLocation")
            or None
        )
        location = cls._extract_location_string(raw_location)

        country_code = prof.get("countryCode") or prof.get("geoCountryUrn") or None
        if not country_code and isinstance(raw_location, dict):
            country_code = raw_location.get("countryCode")
        if country_code and isinstance(country_code, str) and len(country_code) == 2:
            country_code = country_code.upper()
        else:
            country_code = None

        about = prof.get("summary") or prof.get("about") or None
        if about:
            about = str(about).strip() or None

        urn = prof.get("entityUrn") or prof.get("objectUrn") or None
        followers_count = (
            prof.get("followerCount") or prof.get("followersCount") or None
        )
        if isinstance(followers_count, str) and followers_count.isdigit():
            followers_count = int(followers_count)
        elif not isinstance(followers_count, int):
            followers_count = None

        # Resolve Profile Picture URL
        profile_image_url = cls._resolve_picture_url(prof)

        # 3. Resolve Experience Entries
        experience_entries: list[ExperienceEntry] = []
        for pos in parsed.positions:
            exp = cls._resolve_position(pos, urn_index)
            if exp:
                experience_entries.append(exp)

        # 4. Resolve Education Entries
        education_entries: list[EducationEntry] = []
        for edu in parsed.educations:
            entry = cls._resolve_education(edu, urn_index)
            if entry:
                education_entries.append(entry)

        # 5. Resolve Skills
        skills: list[str] = []
        for s in parsed.skills:
            name = s.get("name") or s.get("skillName") or None
            if name and isinstance(name, str) and name.strip():
                clean_name = name.strip()
                if clean_name not in skills:
                    skills.append(clean_name)

        # 6. Resolve Certifications
        certifications: list[CertificationEntry] = []
        for c in parsed.certifications:
            cert_entry = cls._resolve_certification(c)
            if cert_entry:
                certifications.append(cert_entry)

        # 7. Resolve Languages
        languages: list[LanguageEntry] = []
        for l in parsed.languages:
            lang_name = l.get("name") or l.get("languageName") or None
            if lang_name and isinstance(lang_name, str) and lang_name.strip():
                prof_val = l.get("proficiency")
                languages.append(
                    LanguageEntry(
                        name=lang_name.strip(),
                        proficiency=str(prof_val).strip() if prof_val else None,
                    )
                )

        # Derive primary current position/company
        current_pos = experience_entries[0].title if experience_entries else None
        current_comp = experience_entries[0].company if experience_entries else None

        return ResolvedProfileRecords(
            full_name=full_name,
            headline=headline,
            location=location,
            country_code=country_code,
            about=about,
            profile_image_url=profile_image_url,
            urn=urn,
            current_position=current_pos,
            current_company=current_comp,
            followers_count=followers_count,
            experience=experience_entries,
            education=education_entries,
            skills=skills,
            certifications=certifications,
            languages=languages,
        )

    @classmethod
    def _extract_location_string(cls, raw_loc: Any) -> str | None:
        """Extract a clean location string from a raw string or complex ProfileLocation dict."""
        if not raw_loc:
            return None
        if isinstance(raw_loc, str):
            return raw_loc.strip() or None
        if isinstance(raw_loc, dict):
            for key in [
                "preferredGeoPlaceName",
                "geoCountryName",
                "locationName",
                "name",
                "city",
                "countryCode",
            ]:
                val = raw_loc.get(key)
                if isinstance(val, str) and val.strip():
                    return val.strip()
            basic = raw_loc.get("basicLocation")
            if isinstance(basic, dict):
                country = basic.get("countryCode")
                if isinstance(country, str) and country.strip():
                    return country.strip().upper()
        return None

    @classmethod
    def _resolve_picture_url(cls, prof: dict[str, Any]) -> str | None:
        """Extract high-resolution profile picture URL from Voyager picture structure."""
        if "picture" in prof and isinstance(prof["picture"], dict):
            pic = prof["picture"]
            root_url = pic.get("rootUrl", "")
            artifacts = pic.get("artifacts", [])
            if root_url and artifacts and isinstance(artifacts, list):
                # Pick largest artifact or last segment
                last_segment = artifacts[-1].get("fileIdentifyingUrlPathSegment", "")
                if last_segment:
                    return f"{root_url}{last_segment}"

        # Check direct fields
        for key in [
            "profilePicture",
            "photo",
            "displayPictureUrl",
            "profile_image_url",
            "pictureUrl",
        ]:
            val = prof.get(key)
            if val and isinstance(val, str) and val.startswith("http"):
                return val

        return None

    @classmethod
    def _resolve_position(
        cls, pos: dict[str, Any], urn_index: dict[str, dict[str, Any]]
    ) -> ExperienceEntry | None:
        """Resolve a single position entity."""
        title = pos.get("title") or pos.get("jobTitle") or "Untitled Role"
        company = pos.get("companyName") or pos.get("company")

        # Follow company URN if company name missing
        if not company and "*company" in pos:
            company_urn = pos["*company"]
            if company_urn in urn_index:
                company = urn_index[company_urn].get("name") or urn_index[
                    company_urn
                ].get("companyName")

        if not company:
            company = "Unknown Company"

        company_url = pos.get("companyUrl") or pos.get("companyUrn") or None
        location_type = pos.get("locationType") or pos.get("workplaceType") or None
        location = pos.get("locationName") or pos.get("location") or None
        description = pos.get("description") or None

        start_date, end_date = cls._extract_date_range(
            pos.get("dateRange") or pos.get("timePeriod")
        )

        return ExperienceEntry(
            title=str(title).strip(),
            company=str(company).strip(),
            company_url=str(company_url).strip() if company_url else None,
            employment_type=pos.get("employmentType"),
            location_type=str(location_type).strip() if location_type else None,
            location=str(location).strip() if location else None,
            description=str(description).strip() if description else None,
            start_date=start_date,
            end_date=end_date,
        )

    @classmethod
    def _resolve_education(
        cls, edu: dict[str, Any], urn_index: dict[str, dict[str, Any]]
    ) -> EducationEntry | None:
        """Resolve a single education entity."""
        school = edu.get("schoolName") or edu.get("school")
        if not school and "*school" in edu:
            school_urn = edu["*school"]
            if school_urn in urn_index:
                school = urn_index[school_urn].get("name") or urn_index[school_urn].get(
                    "schoolName"
                )
        if not school:
            school = "Unknown Institution"

        degree = edu.get("degreeName") or edu.get("degree") or None
        field_of_study = edu.get("fieldOfStudy") or edu.get("major") or None
        details = edu.get("details") or edu.get("description") or None

        # If degree is absent or combined, parse using regex
        if not degree and details:
            degree, parsed_field = cls.parse_degree(details)
            if not field_of_study and parsed_field:
                field_of_study = parsed_field

        start_date, end_date = cls._extract_date_range(
            edu.get("dateRange") or edu.get("timePeriod")
        )

        return EducationEntry(
            school=str(school).strip(),
            school_url=edu.get("schoolUrl") or edu.get("schoolUrn"),
            details=str(details).strip() if details else None,
            degree=str(degree).strip() if degree else None,
            field_of_study=str(field_of_study).strip() if field_of_study else None,
            start_date=start_date,
            end_date=end_date,
        )

    @classmethod
    def _resolve_certification(cls, cert: dict[str, Any]) -> CertificationEntry | None:
        """Resolve a certification entity."""
        name = cert.get("name") or cert.get("certificationName") or None
        if not name or not str(name).strip():
            return None

        authority = (
            cert.get("authority") or cert.get("issuingOrganization") or "Unknown Issuer"
        )
        license_num = cert.get("licenseNumber") or cert.get("credentialId") or None
        url = cert.get("url") or cert.get("credentialUrl") or None
        start_date, end_date = cls._extract_date_range(
            cert.get("dateRange") or cert.get("timePeriod")
        )

        return CertificationEntry(
            name=str(name).strip(),
            issuing_organization=str(authority).strip(),
            issue_date=start_date,
            expiration_date=end_date,
            credential_id=str(license_num).strip() if license_num else None,
            credential_url=str(url).strip() if url else None,
        )

    @staticmethod
    def _extract_date_range(date_block: Any) -> tuple[str | None, str | None]:
        """Extract start and end date strings from dateRange objects."""
        if not isinstance(date_block, dict):
            return None, None

        start_date = None
        end_date = None

        start_obj = date_block.get("start") or date_block.get("startDate")
        if isinstance(start_obj, dict):
            y = start_obj.get("year")
            m = start_obj.get("month")
            if y and m:
                start_date = f"{y:04d}-{m:02d}"
            elif y:
                start_date = f"{y:04d}"

        end_obj = date_block.get("end") or date_block.get("endDate")
        if isinstance(end_obj, dict):
            y = end_obj.get("year")
            m = end_obj.get("month")
            if y and m:
                end_date = f"{y:04d}-{m:02d}"
            elif y:
                end_date = f"{y:04d}"

        return start_date, end_date

    @classmethod
    def parse_degree(cls, text: str) -> tuple[str | None, str | None]:
        """Split degree string into standard degree name and field of study using regex patterns."""
        if not text:
            return None, None

        cleaned = text.strip()
        for pattern in DEGREE_PATTERNS:
            match = re.search(pattern, cleaned, re.IGNORECASE)
            if match:
                matched_degree = match.group(0).strip()
                remainder = cleaned[: match.start()] + cleaned[match.end() :]
                field_of_study = re.sub(
                    r"^[\s,\-–—|in\s]+|[\s,\-–—|]+$", "", remainder
                ).strip()
                return matched_degree, (field_of_study or None)

        return None, cleaned or None
