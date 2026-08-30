# ProfileForge — Direct LinkedIn Migration Plan

> Historical execution plan. This migration is complete; the plan is retained
> to show the reasoning and verification sequence behind the current direct
> HTTP implementation.

## 1. Overview & Objective
This migration plan details the step-by-step transformation of ProfileForge from an asynchronous cloud-browser polling architecture (LinkedAPI) into a **purely reverse-engineered, browserless direct LinkedIn HTTP provider** adhering to the Tross Software Engineer Hiring Challenge requirements.

---

## 2. Phase-by-Phase Execution Sequence

### Phase 1: Security Remediation (Immediate Priority)
1. **Remove Insecure Routes in `app/main.py`**:
   - Delete `POST /v1/config/credentials` (removes disk write vulnerability and API key exfiltration).
   - Delete `GET /v1/config/status` (removes mock key leakage).
   - Delete `POST /v1/cache/clear` (removes unauthenticated DoS vector).
   - Remove `CredentialUpdateRequest` Pydantic model.
2. **Decouple Client Authentication in `app/auth.py`**:
   - Eliminate `valid_keys.append(settings.LINKEDAPI_TOKEN)`.
   - Ensure `verify_api_key` checks only against `settings.API_KEYS` using constant-time `secrets.compare_digest`.
3. **Refactor Configuration in `app/config.py`**:
   - Delete `save_env_credentials()` function.
   - Remove LinkedAPI settings (`LINKEDAPI_TOKEN`, `LINKEDAPI_IDENTIFICATION_TOKEN`, `LINKEDAPI_POLL_INTERVAL_SECONDS`).
   - Add direct LinkedIn settings: `LINKEDIN_LI_AT`, `LINKEDIN_JSESSIONID`, `LINKEDIN_USER_AGENT`, `LINKEDIN_PROXY_URL`.
   - Update CORS configuration to disable wildcards with credentials.
4. **Harden Frontend Playground in `app/ui.py`**:
   - Remove all LinkedAPI credential management forms, inputs, and JavaScript calls.
   - Preserve URL input, API key input, lookup button, structured view, latency meters, and data quality badges.
5. **Reset `.env` & Verify Git Tracking**:
   - Clear `.env` of any live secrets; keep only development placeholders.
   - Verify `git ls-files .env` returns empty.

### Phase 2: Reverse Engineering Documentation & Direct Provider Implementation
1. **Document Research Findings**:
   - Write `docs/reverse-engineering-notes.md` detailing Voyager endpoint parameters, headers (`csrf-token`, `x-restli-protocol-version`), authentication cookies (`li_at`, `JSESSIONID`), and challenge behavior.
   - Write `docs/extraction-field-map.md` mapping Voyager schema fields (`included[]` entities) to domain models.
   - Write `docs/provider-sequence.md` diagramming the client ➔ request builder ➔ parser ➔ resolver ➔ normalizer flow.
2. **Implement Direct Provider Package (`app/providers/linkedin/`)**:
   - `client.py`: `LinkedInClient` with connection pooling (`httpx.AsyncClient`), Voyager request construction, cookie management, timeout bounds, non-transient error classification, and challenge detection (HTTP 999, captcha, authwall).
   - `parser.py`: `LinkedInParser` extracting raw profile and typed entity dictionaries (`com.linkedin.voyager.dash.identity.profile.*`) from normalized Voyager responses.
   - `resolver.py`: `LinkedInResolver` resolving URN references, entity relationships, degree regex parsing (`DEGREE_PATTERNS`), and media URLs.
   - `normalizer.py`: `LinkedInNormalizer` mapping resolved records into domain `ProfileData` and calculating objective `DataQuality`.
3. **Implement Direct Extractor Adapter (`app/extractor/linkedin_direct.py`)**:
   - Implement `DirectLinkedInExtractor` conforming to `ProfileExtractor` protocol.
   - Wire `DirectLinkedInExtractor` into application dependency injection.

### Phase 3: Core Service Layer Decoupling
1. **Decouple `app/services/profile_service.py`**:
   - Remove all imports of `LinkedAPINormalizer` and LinkedAPI models.
   - Ensure `ProfileService` depends strictly on `ProfileExtractor`, `ProfileData`, and `ProviderCapabilities`.
2. **Decouple `app/extractor/mock.py`**:
   - Remove LinkedAPI imports; provide deterministic, provider-neutral mock datasets (`complete`, `partial`, `minimal`).

### Phase 4: Test Suite Migration & Security Test Harness
1. **Create Security Test Suite (`tests/security/test_endpoint_auth.py`)**:
   - Dynamic router introspection asserting every non-health route requires authentication.
   - Verify rejection of missing/invalid API keys and confirm zero secret leakage.
2. **Create Direct Provider Unit Tests**:
   - `tests/unit/test_linkedin_client.py`: Direct HTTP calls, cookie headers, timeout, challenge detection, error classification.
   - `tests/unit/test_linkedin_parser.py`: Structural validation, entity extraction from `included[]`, missing fields.
   - `tests/unit/test_linkedin_resolver.py`: URN index mapping, degree pattern matching.
   - `tests/unit/test_linkedin_normalizer.py`: `ProfileData` normalization, data quality scoring.
3. **Create Contract & Fixture Tests (`tests/contract/test_voyager_contract.py`)**:
   - Populate `tests/fixtures/raw_upstream/` with sanitized Voyager JSON responses (`voyager_complete.json`, `voyager_partial.json`, `voyager_challenge.json`, etc.).
   - Verify deterministic normalization to `ProfileData`.
4. **Update Integration & E2E Tests**:
   - Update `tests/integration/test_api_flow.py` and `tests/e2e/test_live_smoke.py`.

### Phase 5: Documentation, Infrastructure & Final Cleanup
1. **Archive/Deprecate LinkedAPI**:
   - Remove `app/providers/linkedapi/` and `app/extractor/linkedin.py`.
   - Archive research in `docs/archive/linkedapi/`.
2. **Update Project Documentation**:
   - Update `README.md`, `ARCHITECTURE.md`, `DECISIONS.md`, `REQUIREMENTS.md`, `DEPLOYMENT.md`, `TEST_REPORT.md`.
3. **Update Infrastructure Configuration**:
   - Update `render.yaml`, `Dockerfile`, `docker-compose.yml`, `.env.example`.
4. **Quality Gates & Verification**:
   - Run Ruff, Mypy, Pytest with coverage, and Docker build.
