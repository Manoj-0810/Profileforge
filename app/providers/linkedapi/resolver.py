"""Entity and URN reference resolver for LinkedAPI extracted payloads."""

from __future__ import annotations

import re
from typing import ClassVar

from app.models import EducationEntry, ExperienceEntry, LanguageEntry
from app.providers.linkedapi.parser import (
    ParsedRawProfile,
    RawEducation,
    RawExperience,
    RawLanguage,
)


class LinkedAPIResolver:
    """Resolves URN references, entity links, and structured sub-fields."""

    DEGREE_PATTERNS: ClassVar[list[str]] = [
        r"^(Bachelor of Science|Bachelor of Arts|Bachelor of Engineering|Bachelor of Business Administration|Bachelor['’]s Degree|Bachelor of [A-Za-z]+|B\.?S\.?c?|B\.?A\.?|BS|BA|BEng)",
        r"^(Master of Science|Master of Arts|Master of Business Administration|Master of Engineering|Master['’]s Degree|Master of [A-Za-z]+|M\.?S\.?c?|M\.?A\.?|MS|MA|MEng|MBA)",
        r"^(Doctor of Philosophy|Doctor of [A-Za-z]+|Ph\.?D\.?|Doctorate)",
        r"^(Associate of Science|Associate of Arts|Associate Degree|AS|AA)",
    ]

    def resolve_education_entry(self, raw: RawEducation) -> EducationEntry:
        """Resolve degree and field of study from education details."""
        school = (raw.schoolName or "Unknown Institution").strip()
        details = raw.details.strip() if raw.details else None
        degree: str | None = None
        field_of_study: str | None = None

        if details:
            for pattern in self.DEGREE_PATTERNS:
                match = re.search(pattern, details, re.IGNORECASE)
                if match:
                    degree = match.group(1).strip()
                    remainder = details[match.end() :].strip()
                    # Remove leading 'in', ',', ' - ', etc.
                    remainder = re.sub(
                        r"^(in|,|\-|–|\|)\s*", "", remainder, flags=re.IGNORECASE
                    ).strip()
                    if remainder:
                        field_of_study = remainder
                    break

            if not degree and not field_of_study:
                degree = details

        return EducationEntry(
            school=school,
            school_url=raw.schoolHashedUrl,
            details=details,
            degree=degree,
            field_of_study=field_of_study,
            start_date=raw.startTime,
            end_date=raw.endTime,
        )

    def resolve_experience_entry(self, raw: RawExperience) -> ExperienceEntry:
        """Resolve experience record attributes."""
        title = (raw.position or "Position").strip()
        company = (raw.companyName or "Company").strip()

        return ExperienceEntry(
            title=title,
            company=company,
            company_url=raw.companyHashedUrl,
            employment_type=raw.employmentType,
            location_type=raw.locationType,
            description=raw.description.strip() if raw.description else None,
            duration_months=raw.duration,
            start_date=raw.startTime,
            end_date=raw.endTime,
            location=raw.location.strip() if raw.location else None,
        )

    def resolve_language_entry(self, raw: RawLanguage) -> LanguageEntry:
        """Resolve language name and proficiency."""
        name = (raw.name or raw.language or "Unknown Language").strip()
        proficiency = raw.proficiency.strip() if raw.proficiency else None

        return LanguageEntry(
            name=name,
            proficiency=proficiency,
        )

    def resolve(
        self, parsed: ParsedRawProfile
    ) -> tuple[list[ExperienceEntry], list[EducationEntry], list[LanguageEntry]]:
        """Resolve all sub-entities in a parsed profile."""
        experiences = [
            self.resolve_experience_entry(exp) for exp in parsed.experience_list
        ]
        educations = [
            self.resolve_education_entry(edu) for edu in parsed.education_list
        ]
        languages = [
            self.resolve_language_entry(lang) for lang in parsed.languages_list
        ]

        return experiences, educations, languages
