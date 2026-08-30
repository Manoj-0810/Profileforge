# ProfileForge — Extraction Field Map

## 1. Overview
This document specifies the exact mapping between LinkedIn Voyager upstream JSON structures and ProfileForge domain models (`app/models.py`).

---

## 2. Field Mapping Table

| Domain Field | Target Model | Upstream Entity Type (`$type`) | Upstream JSON Path | Extraction & Normalization Logic | Fallback / Missing Behavior |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `full_name` | `ProfileData` | `*.Profile` | `firstName` + `lastName` | Concatenate non-empty strings with whitespace. | Set to `N/A` if absent. Flag `PARSER_FAILURE` if root profile entity missing. |
| `headline` | `ProfileData` | `*.Profile` | `headline` | Trim leading/trailing whitespace. | `None` (listed in `missing_sections`). |
| `location` | `ProfileData` | `*.Profile` | `locationName` or `geoCountryName` | Trim whitespace. | `None`. |
| `about` | `ProfileData` | `*.Profile` | `summary` | Preserves newline formatting. | `None`. |
| `profile_image_url` | `ProfileData` | `*.Profile` | `picture.rootUrl` + artifact `fileIdentifyingUrlPathSegment` | Concatenates root URL with the largest vector artifact image segment. | `None`. |
| `urn` | `ProfileData` | `*.Profile` | `entityUrn` | e.g. `urn:li:fsd_profile:ACoAAA...` | `None`. |
| `experience[].title` | `ExperienceEntry` | `*.Position` | `title` | Direct string extraction. | `Untitled Role` if blank. |
| `experience[].company` | `ExperienceEntry` | `*.Position` | `companyName` or resolved `companyUrn` | Resolved from entity index if `companyName` is empty. | `Unknown Company`. |
| `experience[].description` | `ExperienceEntry` | `*.Position` | `description` | Multi-line text. | `None`. |
| `experience[].location` | `ExperienceEntry` | `*.Position` | `locationName` | Geographic role location. | `None`. |
| `experience[].start_date` | `ExperienceEntry` | `*.Position` | `dateRange.start` (`year`, `month`) | Formats into `YYYY-MM` or `YYYY`. | `None`. |
| `experience[].end_date` | `ExperienceEntry` | `*.Position` | `dateRange.end` (`year`, `month`) | Formats into `YYYY-MM` or `None` if ongoing. | `None`. |
| `education[].school` | `EducationEntry` | `*.Education` | `schoolName` or resolved `schoolUrn` | Name of academic institution. | `Unknown Institution`. |
| `education[].degree` | `EducationEntry` | `*.Education` | `degreeName` | Extracted and normalized using `DEGREE_PATTERNS` regex parser. | `None`. |
| `education[].field_of_study` | `EducationEntry` | `*.Education` | `fieldOfStudy` | Academic major. | `None`. |
| `education[].start_date` | `EducationEntry` | `*.Education` | `dateRange.start.year` | Formats into `YYYY`. | `None`. |
| `education[].end_date` | `EducationEntry` | `*.Education` | `dateRange.end.year` | Formats into `YYYY`. | `None`. |
| `skills[]` | `ProfileData` | `*.Skill` | `name` | Extracted as clean string array. | `[]`. |
| `certifications[].name` | `CertificationEntry` | `*.Certification` | `name` | Name of license or certificate. | `None`. |
| `certifications[].issuing_organization` | `CertificationEntry` | `*.Certification` | `authority` | Organization issuing credential. | `Unknown Issuer`. |
| `languages[].name` | `LanguageEntry` | `*.Language` | `name` | Language name. | `None`. |
| `languages[].proficiency` | `LanguageEntry` | `*.Language` | `proficiency` | Language proficiency level string. | `None`. |

---

## 3. DataQuality Completeness Calculation

Completeness is calculated deterministically against the supported fields of the direct provider:

$$\text{completeness\_score} = \frac{|\text{available\_sections}|}{|\text{supported\_sections}|}$$

- **Supported Sections (10 Total)**:
  `full_name`, `headline`, `location`, `about`, `experience`, `education`, `skills`, `certifications`, `languages`, `profile_image_url`.
- **Classification Rules**:
  - `available_sections`: Any section present with valid, non-empty data.
  - `missing_sections`: Supported sections that are null, empty, or absent from the target profile.
  - `unavailable_sections`: Sections unsupported by provider capabilities (empty for direct provider).
  - `parser_failed_sections`: Sections where data was present but malformed.
