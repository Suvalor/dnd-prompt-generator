# LLM Frontend/Backend Security Linkage Check

Date: 2026-06-03

Scope:

- Check whether frontend prompt generation is connected to the backend LLM flow.
- Check whether API security, IP quota, browser fingerprint quota, and cookie/session quota are implemented.
- Check whether the implementation is business-ready from the user's Generate Prompt workflow.

## Verdict

Not accepted.

The backend now contains a LLM route, session/CSRF middleware, origin checks, audit logging, and quota logic. However, the frontend prompt generator is still fully browser-local and never calls the backend API. Therefore, the main business flow is not connected:

```text
User clicks Generate prompt
-> frontend uses FORGE.build(...)
-> no /api/session/bootstrap
-> no /api/generate-prompt
-> no CSRF header
-> no session cookie bootstrap
-> no browser fingerprint
-> no backend LLM call
```

So the backend LLM/security implementation exists, but it is not used by the current frontend product flow.

## Blocking Findings

### 1. Frontend Generate Prompt does not call backend LLM

Severity: High

Evidence:

- `dnd-prompt-forge/frontend/js/generator.jsx:190-198`
- `dnd-prompt-forge/frontend/js/generator.jsx:200-202`
- `dnd-prompt-forge/frontend/js/prompt-engine.jsx:76-168`

Current frontend generation path:

```text
runGenerate(data)
-> setTimeout(...)
-> setResult(FORGE.build(data))
```

`FORGE.build()` is a deterministic browser-side prompt builder. It does not call `/api/generate-prompt`, does not receive `mode: llm`, and does not consume backend quota state.

Static search result:

```text
rg "fetch|XMLHttpRequest|axios|/api/|csrf|fingerprint|session/bootstrap|generate-prompt" dnd-prompt-forge/frontend
```

Result:

```text
no matches
```

Impact:

- LLM is not called from the actual UI.
- API quota does not apply to real user prompt generation.
- Cookie/session protection is not exercised by real user prompt generation.
- Browser fingerprint is never generated or sent.
- Frontend cannot switch to backend fallback based on quota because it does not query backend quota.

Required fix:

- Add frontend API client.
- On app boot, call `POST /api/session/bootstrap`.
- Store returned CSRF token in memory.
- Create a browser fingerprint hash.
- On Generate, call `POST /api/generate-prompt` with credentials and CSRF.
- If backend returns `mode: fallback`, display fallback result and quota state.
- If backend is unreachable, use current `FORGE.build()` as local fallback.

### 2. Frontend has no session bootstrap or CSRF integration

Severity: High

Evidence:

- Backend requires session and CSRF for mutating API calls:
  - `dnd-prompt-forge/backend/middleware/csrf.py:25-31`
  - `dnd-prompt-forge/backend/middleware/csrf.py:33-51`
  - `dnd-prompt-forge/backend/middleware/csrf.py:53-92`
- Backend exposes bootstrap:
  - `dnd-prompt-forge/backend/routers/session.py:19-50`
- Frontend has no matching bootstrap/fetch code.

Impact:

Even if frontend later calls `/api/generate-prompt` directly, the request will fail unless it first obtains:

- signed `session_id` HttpOnly cookie;
- signed CSRF token;
- `X-CSRF-Token` header;
- `credentials: "include"` fetch option.

Required fix:

- Add session initialization before first API request.
- Handle bootstrap failure by using non-LLM local mode.
- Keep CSRF token in JS memory, not local storage.

### 3. Browser fingerprint quota is implemented in backend but not supplied by frontend

Severity: High

Evidence:

- Backend accepts fingerprint in request body:
  - `dnd-prompt-forge/backend/routers/generate.py:45`
  - `dnd-prompt-forge/backend/routers/generate.py:80`
- Backend quota checks fingerprint:
  - `dnd-prompt-forge/backend/services/quota.py:59-83`
  - `dnd-prompt-forge/backend/services/quota.py:147-163`
- Frontend contains no fingerprint creation or API submission.

Impact:

The required rule says any one of these conditions should cap LLM use:

```text
same IP OR same browser fingerprint OR same cookie
```

Current real UI flow sends none of them to the backend because it does not call the backend. Even after adding a fetch, fingerprint coverage will still be missing unless the frontend computes and sends `client_fingerprint_hash`.

Required fix:

- Compute a privacy-preserving browser fingerprint hash from stable low-risk signals.
- Send it as `client_fingerprint_hash` in `/api/generate-prompt`.
- Also send it as `X-Fingerprint` when calling `/api/quota`.

### 4. Backend fails open if quota check throws

Severity: High

Evidence:

- `dnd-prompt-forge/backend/routers/generate.py:83-88`

Current behavior:

```text
try:
    quota_result = await check_quota(...)
except Exception:
    quota_result = QuotaResult(allowed=True, limit=10, remaining=10, reset_at="")
```

Impact:

If quota storage or schema fails unexpectedly, the backend allows LLM calls. That weakens the requirement to prevent API extraction/abuse.

Required fix:

- For LLM calls, quota check failure should fail closed into fallback mode.
- Recommended behavior:
  - return deterministic fallback;
  - do not call LLM;
  - log quota failure;
  - expose `mode: fallback`, `quota.remaining: 0`, and a non-sensitive reason.

### 5. Root deployment config omits required security variables

Severity: Medium

Evidence:

- Root `docker-compose.yml:6-11`
- Root `.env.example:1-12`
- App config expects:
  - `SESSION_COOKIE_SECRET`
  - `CSRF_SECRET`
  - `ALLOWED_ORIGINS`
  - `LLM_QUOTA_LIMIT`
  - `REDIS_URL`

Current root compose only passes:

```text
LLM_API_KEY
DB_PATH
LLM_BASE_URL
LLM_MODEL
LLM_TIMEOUT_SECONDS
```

Current root `.env.example` still documents old OpenAI-compatible LLM variables:

```text
LLM_API_KEY
LLM_BASE_URL
LLM_MODEL
```

Impact:

- In production, missing session/CSRF secrets cause runtime-generated random secrets.
- Multiple workers or restarts can invalidate sessions.
- Missing `ALLOWED_ORIGINS` in production means allowed origins default to empty.
- Missing `LLM_QUOTA_LIMIT` makes quota less explicit.

Required fix:

- Update root `.env.example`.
- Pass security variables through root `docker-compose.yml`.
- Make production startup fail or loudly block LLM if required secrets are missing.

### 6. Existing tests validate backend pieces, not frontend/business linkage

Severity: Medium

Evidence:

Targeted backend tests pass when run with `PYTHONPATH=.`:

```text
PYTHONPATH=. python -m pytest tests/test_generate.py tests/test_quota.py tests/test_csrf.py tests/test_session.py -q
44 passed

PYTHONPATH=. python -m pytest tests/test_llm_client.py -q
13 passed
```

But these tests do not verify:

- frontend bootstrap;
- frontend Generate button calling backend;
- CSRF header attached by frontend;
- cookie-based session continuity from browser;
- browser fingerprint submission;
- quota exhaustion forcing frontend-visible fallback.

Also, plain `pytest -q` failed collection in the current shell because the test runner path/environment does not expose backend modules, and the project virtualenv has a broken interpreter path:

```text
./.venv/bin/pytest: bad interpreter: /workspace/dnd-prompt-forge/backend/.venv/bin/python3: no such file or directory
```

Required fix:

- Add `pytest.ini` or equivalent with backend `pythonpath`.
- Recreate or ignore the broken local virtualenv.
- Add integration/browser tests for the actual frontend-to-backend flow.

## What Is Implemented

### Backend LLM route

Implemented.

Evidence:

- `dnd-prompt-forge/backend/routers/generate.py:70-190`
- `dnd-prompt-forge/backend/services/llm_client.py:24-168`

Behavior:

- Checks quota.
- Calls LLM when configured and allowed.
- Falls back to deterministic prompt generation when LLM is unavailable or quota is exceeded.
- Returns `mode`, `request_id`, `quota`, `main_prompt`, `short_prompt`, `negative_prompt`, `style_notes`, and `usage_tip`.

### CSRF and signed cookie session

Implemented in backend.

Evidence:

- `dnd-prompt-forge/backend/routers/session.py:19-50`
- `dnd-prompt-forge/backend/middleware/csrf.py:17-94`
- `dnd-prompt-forge/backend/services/session.py:43-97`

Notes:

- Cookie is `HttpOnly`.
- Cookie uses `SameSite=Lax`.
- Cookie uses `secure=True` when `APP_ENV=production`.

### Origin checking

Implemented in backend.

Evidence:

- `dnd-prompt-forge/backend/middleware/origin.py:18-74`
- `dnd-prompt-forge/backend/config.py:53-59`

Notes:

- Development origins are hardcoded.
- Production origins require `ALLOWED_ORIGINS`.

### Quota by IP, fingerprint, and cookie/session

Implemented in backend service.

Evidence:

- `dnd-prompt-forge/backend/services/quota.py:59-124`
- `dnd-prompt-forge/backend/services/quota.py:127-181`
- `dnd-prompt-forge/backend/services/quota.py:184-245`
- `dnd-prompt-forge/backend/models/database.py:60-75`

Notes:

- Redis path and SQLite fallback exist.
- The check takes the max count across IP/fingerprint/cookie.
- SQLite persistence records hashed identifiers.

### Audit logging

Implemented.

Evidence:

- `dnd-prompt-forge/backend/services/audit.py:36-79`
- `dnd-prompt-forge/backend/models/database.py:77-92`

## Business Acceptance Matrix

| Requirement | Status | Reason |
| --- | --- | --- |
| Frontend prompt generation calls backend LLM | Failed | No frontend API call exists. |
| Backend calls LLM/LLM | Partially passed | Backend route and client exist, but not used by frontend. |
| No API key exposed in frontend | Passed | No frontend provider key found. |
| API requires session cookie | Backend passed, business flow failed | Backend requires it; frontend never bootstraps it. |
| API requires CSRF token | Backend passed, business flow failed | Backend requires it; frontend never sends it. |
| Origin/referer protection | Backend passed | Middleware exists. Production config must be supplied. |
| Same IP 10/hour limit | Backend passed | Implemented in quota service. |
| Same cookie/session 10/hour limit | Backend passed, business flow failed | Backend supports it; frontend never creates session for real generation. |
| Same browser fingerprint 10/hour limit | Backend partial | Backend accepts it; frontend never computes/sends it. |
| Over quota should use non-LLM fallback | Backend partial | Over-quota path does fallback, but quota check exception fails open. |
| Frontend indicates LLM/fallback mode | Failed | Frontend only shows local deterministic output. |
| Automated tests cover backend security | Partially passed | Targeted backend tests pass. Full plain test run does not. |
| Automated tests cover frontend-backend linkage | Failed | No browser/API integration test found. |

## Required Next Implementation Steps

1. Add `frontend/js/api-client.jsx` or equivalent.
2. On app mount, call `POST /api/session/bootstrap` with `credentials: "include"`.
3. Store returned CSRF token in memory.
4. Compute `client_fingerprint_hash`.
5. Change `Generator.runGenerate()` to call backend first.
6. Map frontend fields to backend fields:
   - `type` -> `output_type`
   - `klass` -> `class_role`
   - `desc` -> `description`
   - `model` -> `target_model`
7. On backend success, map response back to frontend `result` shape.
8. On backend unreachable or blocked, use `FORGE.build()` as local fallback.
9. Display `mode` and quota remaining in the output metadata.
10. Change backend quota-check exception behavior to fail closed into fallback.
11. Update root `.env.example` and root `docker-compose.yml` with required security variables.
12. Add browser integration tests:
    - bootstraps session;
    - sends CSRF;
    - sends fingerprint;
    - calls `/api/generate-prompt`;
    - shows LLM mode when backend returns `mode: llm`;
    - shows fallback mode after quota exhaustion.

## Final Acceptance Result

The backend implementation is materially improved and contains most required security components, but the implemented product flow is not connected yet.

Business acceptance should remain blocked until the frontend Generate Prompt action uses the backend LLM API with session, CSRF, fingerprint, and quota-aware fallback handling.
