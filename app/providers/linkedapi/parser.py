"""Structural parser for LinkedAPI completion payloads."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.errors import ErrorCode, ProfileForgeError


class RawExperience(BaseModel):
    model_config = ConfigDict(extra="ignore")
    position: str | None = None
    companyName: str | None = None
    companyHashedUrl: str | None = None
    employmentType: str | None = None
    locationType: str | None = None
    description: str | None = None
    duration: int | None = None
    startTime: str | None = None
    endTime: str | None = None
    location: str | None = None


class RawEducation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    schoolName: str | None = None
    schoolHashedUrl: str | None = None
    details: str | None = None
    startTime: str | None = None
    endTime: str | None = None


class RawSkill(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str | None = None


class RawLanguage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str | None = None
    language: str | None = None
    proficiency: str | None = None


class ParsedRawProfile(BaseModel):
    """Intermediate validated raw profile data before entity resolution."""

    name: str
    headline: str | None = None
    location: str | None = None
    country_code: str | None = None
    about: str | None = None
    profile_image_url: str | None = None
    public_url: str | None = None
    hashed_url: str | None = None
    urn: str | None = None
    current_position: str | None = None
    current_company_name: str | None = None
    current_company_hashed_url: str | None = None
    followers_count: int | None = None
    experience_list: list[RawExperience] = Field(default_factory=list)
    education_list: list[RawEducation] = Field(default_factory=list)
    skills_list: list[str] = Field(default_factory=list)
    languages_list: list[RawLanguage] = Field(default_factory=list)
    parser_failed_sections: list[str] = Field(default_factory=list)


class LinkedAPIParser:
    """Parses and validates raw LinkedAPI completion payloads."""

    def parse(self, raw_completion: dict[str, Any]) -> ParsedRawProfile:
        """Parse raw workflow completion and extract typed intermediate entities."""
        if not isinstance(raw_completion, dict):
            raise ProfileForgeError(
                ErrorCode.UPSTREAM_SCHEMA_CHANGED,
                "Completion payload is not a dictionary",
                status_code=502,
            )

        data = raw_completion.get("data")
        if not isinstance(data, dict):
            raise ProfileForgeError(
                ErrorCode.UPSTREAM_SCHEMA_CHANGED,
                "Completion payload missing 'data' dictionary",
                status_code=502,
            )

        # Top-level name validation
        name = data.get("name")
        if not name or not isinstance(name, str):
            raise ProfileForgeError(
                ErrorCode.UPSTREAM_SCHEMA_CHANGED,
                "Missing or non-string 'name' in profile data payload",
                status_code=502,
            )

        failed_sections: list[str] = []

        # Parse sub-action blocks in then[]
        then_blocks = data.get("then")
        exp_list: list[RawExperience] = []
        edu_list: list[RawEducation] = []
        skills_list: list[str] = []
        lang_list: list[RawLanguage] = []

        if isinstance(then_blocks, list):
            for block in then_blocks:
                if not isinstance(block, dict):
                    continue

                action_type = block.get("actionType")
                action_data = block.get("data")

                if action_type == "st.retrievePersonExperience":
                    if isinstance(action_data, list):
                        for item in action_data:
                            if isinstance(item, dict):
                                exp_list.append(RawExperience(**item))
                    elif action_data is not None:
                        failed_sections.append("experience")

                elif action_type == "st.retrievePersonEducation":
                    if isinstance(action_data, list):
                        for item in action_data:
                            if isinstance(item, dict):
                                edu_list.append(RawEducation(**item))
                    elif action_data is not None:
                        failed_sections.append("education")

                elif action_type == "st.retrievePersonSkills":
                    if isinstance(action_data, list):
                        for item in action_data:
                            if isinstance(item, dict) and item.get("name"):
                                skills_list.append(str(item["name"]))
                            elif isinstance(item, str):
                                skills_list.append(item)
                    elif action_data is not None:
                        failed_sections.append("skills")

                elif action_type == "st.retrievePersonLanguages":
                    if isinstance(action_data, list):
                        for item in action_data:
                            if isinstance(item, dict):
                                lang_list.append(RawLanguage(**item))
                    elif action_data is not None:
                        failed_sections.append("languages")

        elif then_blocks is not None:
            failed_sections.append("nested_actions")

        return ParsedRawProfile(
            name=name.strip(),
            headline=data.get("headline"),
            location=data.get("location"),
            country_code=data.get("countryCode"),
            about=data.get("about") or data.get("summary"),
            profile_image_url=data.get("profilePicture") or data.get("avatar"),
            public_url=data.get("publicUrl"),
            hashed_url=data.get("hashedUrl"),
            urn=data.get("urn"),
            current_position=data.get("position"),
            current_company_name=data.get("companyName"),
            current_company_hashed_url=data.get("companyHashedUrl"),
            followers_count=data.get("followersCount"),
            experience_list=exp_list,
            education_list=edu_list,
            skills_list=skills_list,
            languages_list=lang_list,
            parser_failed_sections=failed_sections,
        )
