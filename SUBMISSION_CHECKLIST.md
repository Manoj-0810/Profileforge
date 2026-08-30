# Tross submission checklist

Use this checklist immediately before sending the repository and hosted URL.

## Functional proof

- [ ] `GET /healthz` returns `200` over HTTPS.
- [ ] `GET /docs` loads and shows the `X-API-Key` security scheme.
- [ ] `POST /v1/profile` succeeds with a valid client key.
- [ ] A repeated lookup demonstrates `cache_hit: true`.
- [ ] An invalid LinkedIn URL returns `INVALID_PROFILE_URL`.
- [ ] An invalid client key returns `401 UNAUTHORIZED`.
- [ ] The deployed service is configured with `EXTRACTOR_TYPE=linkedin` and both LinkedIn session cookies when live extraction is being demonstrated.
- [ ] Run the conditional live smoke test with a real accessible profile URL: `LIVE_TEST_PROFILE_URL=... python -m pytest tests/e2e/test_live_smoke.py -q`.

## Repository hygiene

- [ ] Replace `<YOUR_DEPLOYED_HTTPS_URL>` and `<YOUR_PUBLIC_REPOSITORY_URL>` placeholders in `README.md`.
- [ ] Remove any local `.env` from the commit and confirm `git ls-files .env` is empty.
- [ ] Rotate any session cookie that was ever accidentally exposed outside the deployment secret store.
- [ ] Run the CI commands from `README.md` locally.
- [ ] Include the public repository URL and hosted HTTPS URL in the Tally submission.

## Honest reviewer narrative

Explain that the LinkedIn integration uses direct HTTP requests to LinkedIn's
Voyager endpoints, with `li_at` and `JSESSIONID` kept server-side. State the
known limitations plainly: session expiration, anti-bot challenges, upstream
schema drift, and an in-memory cache that resets on restart. Do not claim that
mock fixture output is live LinkedIn data.
