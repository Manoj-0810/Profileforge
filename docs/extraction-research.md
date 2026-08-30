# ProfileForge — Extraction & Integration Research

> This is the current implementation record. The earlier third-party workflow
> research was archived under `docs/archive/linkedapi/`; it is not part of the
> runtime or submission architecture.

## 1. Requirement and decision

The Tross clarification requires a purely reverse-engineered LinkedIn solution
that directly hits LinkedIn endpoints and does not use a browser. ProfileForge
therefore uses a first-party direct HTTP provider with an authorized LinkedIn
session. The optional HTML playground is only a client for ProfileForge; it is
not involved in LinkedIn acquisition.

Evaluated approaches:

1. **Official LinkedIn API** — not suitable for arbitrary public profile
   lookups under the available independent-developer scopes.
2. **Third-party enrichment/workflow services** — rejected because they add an
   external dependency and do not demonstrate the required direct endpoint
   integration.
3. **Browser automation or cloud browsers** — explicitly excluded by the
   clarification.
4. **Direct Voyager HTTP** — selected: explicit requests, session cookies,
   CSRF derivation, normalized entity parsing, and bounded failure handling.

## 2. Direct HTTP contract

The production adapter is implemented in
`app/providers/linkedin/client.py` and uses `httpx.AsyncClient` only.

```text
GET https://www.linkedin.com/voyager/api/identity/dash/profiles
    ?q=memberIdentity
    &memberIdentity={public_slug}
    &decorationId=com.linkedin.voyager.dash.deco.identity.profile.FullProfileWithEntities-93
```

The request sends:

- `li_at` and `JSESSIONID` as session cookies from an authorized account;
- `csrf-token`, derived from `JSESSIONID` with surrounding quotes removed;
- `x-restli-protocol-version: 2.0.0`;
- LinkedIn's normalized JSON media type and `x-li-lang: en_US` headers;
- a configurable user-agent and optional proxy, without starting a browser.

The client follows no redirects. Authwall, checkpoint, login, rate-limit, and
HTTP 999 responses are classified explicitly so the service does not mistake a
challenge page for profile data or attempt to bypass it.

## 3. Reverse-engineered response pipeline

Voyager returns a normalized entity graph, generally with a root `data` object
and an `included[]` entity store. The implementation keeps each responsibility
separate:

```text
URL validator → request builder/client → parser → URN resolver → normalizer
```

- The parser classifies profile, position, education, skill, certification, and
  language entities from `$type` and structural fields.
- The resolver joins entity references and converts date ranges and location
  metadata into domain values.
- The normalizer produces the stable public `ProfileData` schema and a
  deterministic data-quality report, including unavailable sections.

The sanitized Voyager fixtures in `tests/fixtures/raw_upstream/` are the
offline contract for this behavior. A live smoke test is available at
`tests/e2e/test_live_smoke.py` and runs only when both session cookies are
provided explicitly.

## 4. Evidence and verification boundary

The repository verifies the HTTP contract, cookie/CSRF construction, parser
behavior, error mapping, caching, concurrency, security controls, and API
schema entirely offline. It does not claim that a live LinkedIn session is
valid without credentials; the live smoke test is intentionally conditional.

LinkedIn's internal endpoint and decoration identifiers can change. A
production deployment must therefore record the date of its live smoke test,
keep credentials in deployment secrets, and rotate the endpoint contract when
LinkedIn changes its response shape.

## 5. Security boundary

- Public callers authenticate with ProfileForge's `X-API-Key`; that key is
  never reused as an upstream credential.
- LinkedIn session cookies are server-side environment secrets and are never
  accepted in request bodies or returned in responses.
- Logs redact cookies, API keys, authorization headers, and CSRF material.
- The service detects challenges and rate limits and fails closed; it performs
  no credential harvesting, CAPTCHA solving, browser emulation, or evasion.
