# ProfileForge — Reverse-Engineering Research Notes

## 1. Overview & Scope
This document details the reverse-engineered HTTP communication contract between browserless clients and LinkedIn's internal REST API (Voyager) for retrieving public and member profile representations without browser emulation.

---

## 2. Verified Endpoints & Query Signatures

### 2.1 Primary Profile Representation Endpoint
- **URL**: `https://www.linkedin.com/voyager/api/identity/dash/profiles`
- **Method**: `GET`
- **Query Parameters**:
  - `q=memberIdentity`: Parameterized query filter for member resolution.
  - `memberIdentity={public_slug}`: The public identifier extracted from the canonical profile URL (e.g. `sarah-jenkins-dev`).
  - `decorationId=com.linkedin.voyager.dash.deco.identity.profile.FullProfileWithEntities-93`: Projection filter declaring the entity subgraph to expand and include in the response payload.

### 2.2 Alternative / Profile View Endpoint (Observed, not used by the adapter)
- **URL**: `https://www.linkedin.com/voyager/api/identity/profiles/{public_slug}/profileView`
- **Method**: `GET`
- **Query Parameters**: None or standard RestLi query parameters.

---

## 3. Request Headers & Session Authentication

Direct HTTP communication with Voyager requires an authorized user session. Authentication and CSRF mitigation use the following header-cookie pairing:

| Header / Cookie | Type | Description |
| :--- | :--- | :--- |
| `Cookie: li_at=...` | Cookie | Primary HTTP-only session token authorizing the LinkedIn account. |
| `Cookie: JSESSIONID="..."` | Cookie | Session identifier token, often wrapped in double quotes. |
| `csrf-token: ...` | Header | CSRF validation token matching the exact string in `JSESSIONID` with quotes removed. |
| `x-restli-protocol-version: 2.0.0` | Header | Required LinkedIn Rest.li protocol version header. |
| `accept: application/vnd.linkedin.normalized+json+2.1` | Header | Tells Voyager to serialize data into the normalized entity store format. |
| `x-li-lang: en_US` | Header | Standard localization header. |
| `User-Agent: Mozilla/5.0...` | Header | Realistic modern desktop browser user-agent. |

---

## 4. Upstream Normalized JSON Response Structure

Voyager APIs return a **normalized entity graph** rather than deeply nested hierarchical JSON.

### Key Top-Level Fields:
- `data`: Root object containing primary entity references (e.g. `*elements`, `*profile`).
- `included`: A flat array containing all resolved domain entity objects. Every entity contains:
  - `$type`: The fully qualified schema type string (e.g. `com.linkedin.voyager.dash.identity.profile.Position`).
  - `entityUrn`: Unique URN string identifying this node in the graph (e.g. `urn:li:fsd_profilePosition:(MEMBER_URN,POSITION_ID)`).

### Recognized Entity Types:
1. `com.linkedin.voyager.dash.identity.profile.Profile`:
   - Contains: `firstName`, `lastName`, `headline`, `locationName`, `summary`, `entityUrn`, `objectUrn`, `picture`.
2. `com.linkedin.voyager.dash.identity.profile.Position`:
   - Contains: `title`, `companyName`, `companyUrn`, `description`, `locationName`, `dateRange` (`start`, `end`).
3. `com.linkedin.voyager.dash.identity.profile.Education`:
   - Contains: `schoolName`, `schoolUrn`, `degreeName`, `fieldOfStudy`, `dateRange` (`start`, `end`).
4. `com.linkedin.voyager.dash.identity.profile.Skill`:
   - Contains: `name`, `entityUrn`.
5. `com.linkedin.voyager.dash.identity.profile.Certification`:
   - Contains: `name`, `authority`, `url`, `licenseNumber`, `dateRange`.
6. `com.linkedin.voyager.dash.identity.profile.Language`:
   - Contains: `name`, `proficiency`.

---

## 5. Failure Modes & Challenge Detection

Because ProfileForge operates strictly without browser emulation, all security boundaries and anti-bot responses are detected cleanly and mapped to deterministic error codes without attempting evasion:

| Upstream Indicator | Status Code | Classification | Application Error Code | Action |
| :--- | :--- | :--- | :--- | :--- |
| Invalid / Expired `li_at` | 401 Unauthorized | Session expired | `UPSTREAM_AUTH_FAILED` | Fail immediately; do NOT retry |
| CSRF mismatch / 403 | 403 Forbidden | CSRF token invalid | `UPSTREAM_AUTH_FAILED` | Fail immediately; log diagnostic |
| Member slug does not exist | 404 Not Found | Profile not found | `PROFILE_NOT_FOUND` | Return 404 to caller |
| HTTP 999 Request Denied | 999 / 429 | Rate limit / Bot check | `UPSTREAM_RATE_LIMITED` | Return 502 + Retry-After |
| Redirect to `/authwall` or `/checkpoint/` | 302 / 303 | Bot challenge | `UPSTREAM_CHALLENGE_DETECTED` | Fail cleanly; document challenge |
| Upstream 500 / 502 / 503 | 5xx | Transient failure | `UPSTREAM_SERVER_ERROR` | Bounded retry (up to 2 retries / 3 total attempts) |
| Timeout (>30s) | Timeout | Latency / drop | `UPSTREAM_TIMEOUT` | Return 504 Gateway Timeout |
| Missing expected `$type` keys | 200 OK | Schema drift | `UPSTREAM_SCHEMA_CHANGED` | Return partial data + log warning |

---

## 6. Assumptions & Limitations
1. **Session Longevity**: `li_at` session cookies last between 30 and 90 days before requiring rotation in the backend environment.
2. **Decoration Versioning**: LinkedIn periodically increments decoration ID suffixes (e.g. `-93` ➔ `-94`). The parser must handle unrecognized entity decorators gracefully via fallback structural extraction.
3. **No Credential Harvesting**: The API does not accept credentials via public requests; all session material is securely supplied via environment variables.
