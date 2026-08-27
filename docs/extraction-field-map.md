# ProfileForge — Extraction Field Map & Provider Capabilities

## 1. Overview & Verification Status

This document defines the field-level contract between the upstream provider payload and the normalized `ProfileData` domain model, incorporating dynamic **Provider Capabilities** for deterministic data quality and completeness scoring.

---

## 2. ProviderCapabilities Abstraction

Providers explicitly declare their supported extraction capabilities so the application evaluates data quality relative to what the active provider can actually extract, rather than penalizing profiles for provider-unsupported attributes.

```python
class ProviderCapabilities(BaseModel):
    provider_name: str
    supported_sections: set[str]  # e.g., {"full_name", "headline", "location", "experience", "education", "skills", "languages"}
    unsupported_sections: set[str]  # e.g., {"certifications", "about", "profile_image_url"}
    supports_realtime_polling: bool = True
    max_recommended_concurrency: int = 2
```

---

## 3. Comprehensive Field Mapping Matrix

| Output Field | Provider Action / Source | Upstream Field Path | Entity / Reference | Transformation | Fallback | Unavailable Behavior | Parser Failure Behavior | Test Fixture |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `full_name` | `st.openPersonPage` (basicInfo: true) | `data.name` | Direct string | Strip whitespace | `None` | `missing_sections += "full_name"` | `PARSER_FAILURE` if non-string | `complete_profile.json` |
| `headline` | `st.openPersonPage` (basicInfo: true) | `data.headline` | Direct string | Trim whitespace | `None` | `missing_sections += "headline"` | `PARSER_FAILURE` if invalid type | `complete_profile.json` |
| `location` | `st.openPersonPage` (basicInfo: true) | `data.location` | Direct string | Trim whitespace | `None` | `missing_sections += "location"` | `PARSER_FAILURE` if invalid type | `complete_profile.json` |
| `country_code` | `st.openPersonPage` (basicInfo: true) | `data.countryCode` | ISO 3166-1 alpha-2 | Uppercase 2-char code | `None` | `null` | `PARSER_FAILURE` if non-string | `complete_profile.json` |
| `about` | `st.openPersonPage` (basicInfo: true) | `data.about` / `data.summary` | Direct string | Trim whitespace | `None` | `unavailable_sections += "about"` (if unexposed) | `PARSER_FAILURE` if invalid type | `missing_about.json` |
| `profile_image_url` | `st.openPersonPage` (basicInfo: true) | `data.profilePicture` / `data.avatar` | URL string | Validate HTTPS format | `None` | `unavailable_sections += "profile_image_url"` | `PARSER_FAILURE` if malformed URL | `missing_image.json` |
| `profile_url` | `st.openPersonPage` (basicInfo: true) | `data.publicUrl` | URL string | Canonicalize format | Input canonical URL | Always populated | `PARSER_FAILURE` if unparseable | `complete_profile.json` |
| `urn` | `st.openPersonPage` (basicInfo: true) | `data.urn` | Member URN (`urn:li:member:...`) | Validate prefix | `None` | `null` | `PARSER_FAILURE` if non-string | `complete_profile.json` |
| `current_position` | `st.openPersonPage` (basicInfo: true) | `data.position` | Direct string | Trim whitespace | First entry of `experience` | `null` | `PARSER_FAILURE` if invalid type | `complete_profile.json` |
| `current_company` | `st.openPersonPage` (basicInfo: true) | `data.companyName` | Direct string | Trim whitespace | First entry company of `experience` | `null` | `PARSER_FAILURE` if invalid type | `complete_profile.json` |
| `followers_count` | `st.openPersonPage` (basicInfo: true) | `data.followersCount` | Integer | Integer conversion | `None` | `null` | `PARSER_FAILURE` if non-int | `complete_profile.json` |
| `experience[]` | `st.retrievePersonExperience` | `then[].data[]` | Array of objects | Map each item to `ExperienceEntry` | `[]` | `missing_sections += "experience"` | `PARSER_FAILURE` if non-list | `multiple_experience.json` |
| `education[]` | `st.retrievePersonEducation` | `then[].data[]` | Array of objects | Map each item to `EducationEntry` | `[]` | `missing_sections += "education"` | `PARSER_FAILURE` if non-list | `multiple_education.json` |
| `skills[]` | `st.retrievePersonSkills` | `then[].data[]` | Array of objects / strings | Extract skill name strings | `[]` | `missing_sections += "skills"` | `PARSER_FAILURE` if malformed | `skills_only.json` |
| `certifications[]` | `st.retrievePersonCertifications` (Provisional) | `then[].data[]` | Array of objects | Map to `CertificationEntry` | `[]` | `unavailable_sections += "certifications"` | `PARSER_FAILURE` if malformed | `partial_profile.json` |
| `languages[]` | `st.retrievePersonLanguages` | `then[].data[]` | Array of objects | Map to `LanguageEntry` | `[]` | `missing_sections += "languages"` | `PARSER_FAILURE` if malformed | `languages_response.json` |

---

## 4. Provider-Aware Data Quality & Completeness Model

### 4.1 Categorization Rules
Let:
- $C$ = set of sections supported by the active provider (`ProviderCapabilities.supported_sections`).
- $U$ = set of sections unsupported/unexposed by the provider (`ProviderCapabilities.unsupported_sections`).
- $A \subseteq C$ = set of supported sections successfully extracted and non-empty.
- $M = C \setminus A$ = set of supported sections that are empty or null on the target profile.
- $F$ = set of sections where parser encountered structural schema failures.

### 4.2 Mathematical Formula
The provider-aware completeness score $S$ is calculated strictly against supported sections $C$:
$$S = \begin{cases} \frac{|A|}{|C|} & \text{if } |C| > 0 \\ 0.0 & \text{otherwise} \end{cases}$$

Where $S \in [0.0, 1.0]$, rounded to 2 decimal places.

### 4.3 Response Contract
```json
{
  "data_quality": {
    "available_sections": ["full_name", "headline", "location", "experience", "education", "skills"],
    "missing_sections": ["languages"],
    "unavailable_sections": ["certifications", "about", "profile_image_url"],
    "parser_failed_sections": [],
    "completeness_score": 0.86
  }
}
```
If schema drift causes a field to fail parsing, it is appended to `parser_failed_sections` and tracked in metrics without fabricating data.
