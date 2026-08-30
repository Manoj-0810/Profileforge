"""Parser for raw LinkedIn Voyager normalized JSON payloads."""

from __future__ import annotations

from typing import Any

import structlog
from pydantic import BaseModel, ConfigDict, Field

from app.errors import ErrorCode, ProfileForgeError

logger = structlog.get_logger(__name__)


class ParsedVoyagerData(BaseModel):
    """Intermediate structured container holding categorized raw entities."""

    model_config = ConfigDict(extra="ignore")

    profile_entity: dict[str, Any] = Field(default_factory=dict)
    positions: list[dict[str, Any]] = Field(default_factory=list)
    educations: list[dict[str, Any]] = Field(default_factory=list)
    skills: list[dict[str, Any]] = Field(default_factory=list)
    certifications: list[dict[str, Any]] = Field(default_factory=list)
    languages: list[dict[str, Any]] = Field(default_factory=list)
    raw_entities: list[dict[str, Any]] = Field(default_factory=list)
    schema_drift_detected: bool = False
    parser_failed_sections: list[str] = Field(default_factory=list)


class LinkedInParser:
    """Parses normalized Voyager responses and groups entities by schema type."""

    @classmethod
    def parse(cls, raw_response: dict[str, Any]) -> ParsedVoyagerData:
        """Parse normalized Voyager JSON into categorized entity records.

        Args:
            raw_response: Raw dictionary from LinkedIn Voyager HTTP response.

        Returns:
            ParsedVoyagerData containing extracted entities and schema quality flags.

        Raises:
            ProfileForgeError: If response is fundamentally unparseable or lacks required structure.
        """
        if not isinstance(raw_response, dict):
            raise ProfileForgeError(
                ErrorCode.UPSTREAM_SCHEMA_CHANGED,
                "Expected JSON object at root of LinkedIn response.",
                status_code=502,
            )

        entities: list[dict[str, Any]] = []

        # 1. Extract entities from 'included' list (standard Voyager format)
        if "included" in raw_response and isinstance(raw_response["included"], list):
            entities.extend(
                item for item in raw_response["included"] if isinstance(item, dict)
            )

        # 2. Extract from 'data' if present
        data_block = raw_response.get("data")
        if isinstance(data_block, dict):
            # Check for elements array inside data
            elements = data_block.get("elements")
            if isinstance(elements, list):
                entities.extend(item for item in elements if isinstance(item, dict))
            # Or if data itself is a profile entity
            if "$type" in data_block or "firstName" in data_block:
                entities.append(data_block)

        # 3. Fallback: If root response has profile fields directly (legacy or mock format)
        if not entities and ("firstName" in raw_response or "name" in raw_response):
            entities.append(raw_response)

        if not entities:
            logger.warning("empty_entities_in_voyager_response")
            return ParsedVoyagerData(
                schema_drift_detected=True,
                parser_failed_sections=["full_name", "headline", "location"],
            )

        profile_entity: dict[str, Any] = {}
        positions: list[dict[str, Any]] = []
        educations: list[dict[str, Any]] = []
        skills: list[dict[str, Any]] = []
        certifications: list[dict[str, Any]] = []
        languages: list[dict[str, Any]] = []
        parser_failed_sections: list[str] = []

        for entity in entities:
            entity_type = entity.get("$type", "").lower()
            lower_keys = [k.lower() for k in entity]

            # Profile classification
            if "profile" in entity_type and (
                "firstname" in lower_keys or "headline" in lower_keys
            ):
                if not profile_entity:
                    profile_entity = entity
                else:
                    # Merge additional profile fields if found
                    profile_entity = {**entity, **profile_entity}

            # Direct root profile match without explicit $type
            elif not profile_entity and ("firstName" in entity or "headline" in entity):
                profile_entity = entity

            # Position / Experience
            elif "position" in entity_type or "experience" in entity_type:
                positions.append(entity)

            # Education
            elif "education" in entity_type or "school" in entity_type:
                educations.append(entity)

            # Skill
            elif "skill" in entity_type:
                skills.append(entity)

            # Certification
            elif "certification" in entity_type or "license" in entity_type:
                certifications.append(entity)

            # Language
            elif "language" in entity_type:
                languages.append(entity)

        # Fallback profile search if not matched by type
        if not profile_entity:
            for entity in entities:
                if any(
                    k in entity
                    for k in ["firstName", "lastName", "headline", "summary", "name"]
                ):
                    profile_entity = entity
                    break

        drift = not bool(profile_entity)
        if drift:
            logger.warning(
                "schema_drift_missing_profile_entity", entity_count=len(entities)
            )
            parser_failed_sections.append("profile_root")

        return ParsedVoyagerData(
            profile_entity=profile_entity,
            positions=positions,
            educations=educations,
            skills=skills,
            certifications=certifications,
            languages=languages,
            raw_entities=entities,
            schema_drift_detected=drift,
            parser_failed_sections=parser_failed_sections,
        )
