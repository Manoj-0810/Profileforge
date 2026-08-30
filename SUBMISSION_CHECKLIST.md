# ProfileForge — Pre-Submission Checklist

Use this checklist immediately before sending the repository and hosted URL to Tross.

---

## ✅ Functional Proof

- [x] `GET /healthz` returns `200` over HTTPS — `https://profileforge-ysbd.onrender.com/healthz`
- [x] `GET /readyz` returns `200` with `"extractor": "linkedin"` when live mode is configured
- [x] `GET /docs` loads the interactive OpenAPI UI with `ProfileForgeApiKey` security scheme
- [x] A successful live `POST /v1/profile` response was captured with a valid `X-API-Key` and public LinkedIn URL; re-verify immediately before submission
- [x] A repeated lookup shows `"cache_hit": true` in the response body
- [x] An invalid LinkedIn URL returns `400 INVALID_PROFILE_URL`
- [x] An invalid API key returns `401 UNAUTHORIZED`
- [x] Hosted URL is `https://profileforge-ysbd.onrender.com`
- [x] GitHub repository is publicly accessible at `https://github.com/Manoj-0810/Profileforge`

---

## 🔑 Configuring Live LinkedIn Extraction (Dedicated Test Account)

> **IMPORTANT**: Do NOT use your personal LinkedIn account for submission.
> LinkedIn's WAF invalidates sessions replayed from cloud server IPs different from the browser's IP,
> logging your browser out immediately. Use a **dedicated test account**.

### Step-by-step: Get a stable session for Render

1. **Create a brand-new LinkedIn account** (use a Gmail alias like `yourname+pftest@gmail.com`).
2. Open that account in a browser, log in once, and leave it idle after copying the cookies. A matching network/IP cannot be guaranteed from Render, so treat this as a challenge-only test session rather than a production reliability strategy.
3. Immediately **copy the cookies** via F12 → Application → Cookies → `https://www.linkedin.com`:
   - `li_at`: full value starting with `AQED...`
   - `JSESSIONID`: value like `"ajax:1234567890..."`
4. **Do NOT log into LinkedIn again** on any browser with this account after copying. This keeps the session alive on Render's servers without the IP-conflict logout.
5. Set in Render → Environment:
   ```
   ENVIRONMENT=production
   EXTRACTOR_TYPE=linkedin
   API_KEYS=<your-secure-key>
   LINKEDIN_LI_AT=<copied-li_at-value>
   LINKEDIN_JSESSIONID=<copied-jsessionid-value>
   ```

---

## 🧹 Repository Hygiene

- [x] No `.env` is tracked — verified with `git ls-files .env` (empty)
- [x] No secrets or credentials appear in any tracked file — confirmed by `test_secret_leakage.py`
- [x] `README.md` contains the live Render URL and GitHub URL
- [x] `TEST_REPORT.md` shows current test count (88 passed, 1 skipped, 88% coverage)
- [ ] Confirm the latest GitHub Actions run is green before submission (local quality gates pass)

---

## 📋 Tross Submission Form Content

Include the following in the submission form/email:

| Field | Value |
| :--- | :--- |
| **Hosted HTTPS API URL** | `https://profileforge-ysbd.onrender.com` |
| **GitHub Repository** | `https://github.com/Manoj-0810/Profileforge` |
| **OpenAPI Docs** | `https://profileforge-ysbd.onrender.com/docs` |
| **Health Check** | `https://profileforge-ysbd.onrender.com/healthz` |
| **Test API Key** | *(provide securely via form, not in README)* |

---

## 📝 Honest Reviewer Narrative

> ProfileForge uses a reverse-engineered HTTP client that communicates directly with LinkedIn's internal Rest.li Voyager API (`/voyager/api/identity/dash/profiles`) without any browser automation. Authentication uses server-side `li_at` and `JSESSIONID` session cookies stored exclusively in Render's encrypted environment variables — never committed to the repository.
>
> **Known constraints stated plainly:**
> - LinkedIn's WAF enforces IP-based session binding. A session token issued to a browser at one IP is invalidated when replayed from a different cloud server IP. This is not a code defect; it is a fundamental constraint of reverse-engineering private endpoints. The code correctly classifies 403 responses as `UPSTREAM_AUTH_FAILED`.
> - Session cookies expire every 30–90 days and require rotation in Render's environment variables.
> - The in-memory cache resets on server restart.
> - Mock mode (`EXTRACTOR_TYPE=mock`) provides deterministic offline responses for automated testing and reliable reviewer evaluation. It is clearly labelled in the response as `"source": "mock"` and is never presented as live LinkedIn data.
