# ProfileForge — Requirements Traceability Matrix

## 1. Traceability Principle
Every requirement from the Tross Hiring Challenge is assigned an immutable identifier and mapped to its implementing module, automated test suite, live verification mechanism, and verified status with concrete evidence.

---

## 2. Core Functional Requirements

| ID | Requirement | Implementing Module | Automated Test File | Live Verification Method | Evidence Artifact | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **R01** | Accept LinkedIn profile URL | `app/services/url_utils.py`, `app/main.py` | `tests/unit/test_url_utils.py`, `tests/integration/test_api_flow.py` | POST to `/v1/profile` with valid URL | HTTP 200 + response JSON | **VERIFIED** |
| **R02** | Return structured JSON | `app/models.py`, `app/main.py` | `tests/unit/test_models.py`, `tests/integration/test_api_flow.py` | Inspect response body | Validated Pydantic schema | **VERIFIED** |
| **R03** | Full Name extraction | `app/providers/linkedin/resolver.py` | `tests/contract/test_voyager_contract.py`, `test_linkedin_resolver.py` | Direct Voyager lookup | `profile.full_name` populated | **VERIFIED** |
| **R04** | Headline extraction | `app/providers/linkedin/resolver.py` | `tests/contract/test_voyager_contract.py`, `test_linkedin_resolver.py` | Direct Voyager lookup | `profile.headline` populated | **VERIFIED** |
| **R05** | Location extraction | `app/providers/linkedin/resolver.py` | `tests/contract/test_voyager_contract.py`, `test_linkedin_resolver.py` | Direct Voyager lookup | `profile.location` populated | **VERIFIED** |
| **R06** | About / Summary extraction | `app/providers/linkedin/resolver.py` | `tests/contract/test_voyager_contract.py`, `test_linkedin_resolver.py` | Direct Voyager lookup | `profile.about` (string or null) | **VERIFIED** |
| **R07** | Experience list extraction | `app/providers/linkedin/resolver.py` | `tests/contract/test_voyager_contract.py`, `test_linkedin_resolver.py` | Direct Voyager lookup | `profile.experience[]` list | **VERIFIED** |
| **R08** | Education list extraction | `app/providers/linkedin/resolver.py` | `tests/contract/test_voyager_contract.py`, `test_linkedin_resolver.py` | Direct Voyager lookup | `profile.education[]` list | **VERIFIED** |
| **R09** | Skills list extraction | `app/providers/linkedin/resolver.py` | `tests/contract/test_voyager_contract.py`, `test_linkedin_resolver.py` | Direct Voyager lookup | `profile.skills[]` list | **VERIFIED** |
| **R10** | Certifications list extraction | `app/providers/linkedin/resolver.py` | `tests/contract/test_voyager_contract.py`, `test_linkedin_resolver.py` | Direct Voyager lookup | `profile.certifications[]` list | **VERIFIED** |
| **R11** | Languages list extraction | `app/providers/linkedin/resolver.py` | `tests/contract/test_voyager_contract.py`, `test_linkedin_resolver.py` | Direct Voyager lookup | `profile.languages[]` list | **VERIFIED** |
| **R12** | Profile picture URL | `app/providers/linkedin/resolver.py` | `tests/contract/test_voyager_contract.py`, `test_linkedin_resolver.py` | Direct Voyager lookup | `profile.profile_image_url` URL or null | **VERIFIED** |
| **R13** | Public deployment over HTTPS | Docker on Render.com | `tests/integration/test_diagnostics.py`, `render.yaml` | Run `GET /healthz` against deployed URL | Must be verified after deployment | **READY / LIVE CHECK REQUIRED** |
| **R14** | Browserless direct HTTP access | `app/providers/linkedin/client.py` | `tests/unit/test_linkedin_client.py` | Direct HTTP GET to Voyager fixture contract | Cookie + CSRF construction verified offline; live smoke is conditional | **OFFLINE VERIFIED** |
| **R15** | Public Git Repository | Root workspace | `git status`, `git log` | Review GitHub repository | Must be populated with the public repository URL | **SUBMISSION CHECK REQUIRED** |
| **R16** | Comprehensive README | `README.md` | Manual hiring-grade review | Markdown rendering check | Complete documentation in README.md | **VERIFIED** |
| **R17** | Zero Secrets in Repository | `.gitignore`, `.env.example` | Repository secret scan script | `git grep` / `git ls-files` | Audit evidence in `TEST_REPORT.md` | **VERIFIED** |
| **R18** | Custom Response Schema | `app/models.py` | `tests/unit/test_models.py` | OpenAPI docs `/docs` | OpenAPI JSON schema | **VERIFIED** |

---

## 3. Architecture & Reliability Requirements

| ID | Requirement | Implementing Module | Automated Test File | Status |
| :--- | :--- | :--- | :--- | :--- |
| **A01** | Provider Independence | `app/extractor/base.py` (Protocol) | `tests/unit/test_models.py`, `tests/unit/test_single_flight.py` | **VERIFIED** |
| **A02** | Layered Adapter Pipeline | `app/providers/linkedin/` | `tests/contract/test_voyager_contract.py` | **VERIFIED** |
| **A03** | Direct HTTP Rest.li Client | `app/providers/linkedin/client.py` | `tests/unit/test_linkedin_client.py` | **VERIFIED** |
| **A04** | In-Memory Caching (Canonical ID) | `app/cache.py` | `tests/unit/test_cache.py`, `tests/integration/test_cache_behavior.py` | **VERIFIED** |
| **A05** | Bounded Concurrency Semaphore | `app/services/profile_service.py` | `tests/unit/test_single_flight.py` | **VERIFIED** |
| **A06** | Sliding Window Rate Limiting | `app/rate_limit.py` | `tests/unit/test_rate_limiter.py` | **VERIFIED** |
| **A07** | Strict URL Validation & SSRF Guard | `app/services/url_utils.py` | `tests/unit/test_url_utils.py` | **VERIFIED** |
| **A08** | Schema-Drift Detection | `app/providers/linkedin/parser.py` | `tests/contract/test_voyager_contract.py` | **VERIFIED** |
| **A09** | Upstream Error Classification | `app/errors.py`, `app/providers/linkedin/client.py` | `tests/unit/test_errors.py`, `tests/integration/test_error_responses.py` | **VERIFIED** |
| **A10** | Structured JSON Logging & Request ID | `app/logging_config.py` | `tests/integration/test_api_flow.py` | **VERIFIED** |
| **A11** | Deterministic Data Quality Scoring | `app/providers/linkedin/normalizer.py` | `tests/unit/test_linkedin_normalizer.py` | **VERIFIED** |
| **A12** | Single-Flight Request Coalescing | `app/services/profile_service.py` | `tests/unit/test_single_flight.py` | **VERIFIED** |
| **A13** | ProviderCapabilities Abstraction | `app/models.py`, `app/providers/linkedin/normalizer.py` | `tests/unit/test_models.py`, `tests/unit/test_linkedin_normalizer.py` | **VERIFIED** |
| **A14** | Dynamic Router Authentication Audit | `tests/security/test_endpoint_auth.py` | `tests/security/test_endpoint_auth.py` | **VERIFIED** |
