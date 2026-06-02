# LLM Multimodal Prompt Generation And Abuse Protection

Date: 2026-06-02
Status: scope proposal
Project: DND Prompt Forge

## Goal

Add backend-controlled LLM prompt generation for DND Prompt Forge while keeping the existing browser-only deterministic generator as the fallback path.

The new backend must support:

- Text-to-prompt generation with MiMo.
- Image analysis input for prompt generation.
- Video analysis input for prompt generation.
- API interface authentication and abuse protection.
- Server-side quota control: same IP, same browser fingerprint, or same cookie may call the LLM at most 10 times per hour. After that, the backend must not call the LLM and must instruct the frontend to use no-LLM mode.

## External API Notes

Official MiMo docs reviewed:

- Token Plan subscription docs: https://platform.xiaomimimo.com/docs/zh-CN/price/tokenplan/subscription
- Image understanding docs: https://platform.xiaomimimo.com/docs/zh-CN/usage-guide/multimodal-understanding/image-understanding
- Video understanding docs: https://platform.xiaomimimo.com/docs/zh-CN/usage-guide/multimodal-understanding/video-understanding

Important constraints from the docs:

- Image understanding supports image URL and Base64 input.
- Image Base64 payload must include `data:{MIME_TYPE};base64,$BASE64_IMAGE`; converted Base64 string size must not exceed 50 MB.
- Image URL file size must not exceed 50 MB.
- Video understanding supports video URL and Base64 input.
- Video URL file size must not exceed 300 MB.
- Video Base64 payload must include `data:{MIME_TYPE};base64,$BASE64_VIDEO`; converted Base64 string size must not exceed 50 MB.
- Image/video understanding currently supports `mimo-v2.5` and `mimo-v2-omni`.
- Token Plan docs state that Token Plan quota is intended for AI coding tools and prohibit API-call usage in custom application backends or other obvious non-coding scenarios.

Compliance requirement:

- Do not use a Token Plan subscription API key for the production public app unless Xiaomi explicitly permits this use case.
- Prefer ordinary API billing credentials for the deployed application.
- Keep the provider configuration generic so either a permitted Token Plan-compatible endpoint or ordinary MiMo API endpoint can be selected by environment variables.

## LLM Credential Modes

To allow backend LLM calls while avoiding accidental misuse of subscription credentials, the backend must support explicit credential modes.

Environment variable:

```text
LLM_CREDENTIAL_MODE=production_api
```

Allowed values:

### `production_api`

Purpose:

- Public deployed web application.
- Backend may call MiMo for anonymous end users after quota/auth checks pass.
- Use only API credentials that are permitted for custom application backend usage.

Rules:

- Requires `MIMO_API_KEY`.
- Requires strict origin/CORS allowlist.
- Requires signed session cookie and nonce.
- Requires hourly quota enforcement.
- Allows text, image, and video LLM calls if feature flags permit.

### `subscription_dev`

Purpose:

- Local development, internal testing, or operator-only debugging when the credential source is a subscription/token-plan style credential that may not be allowed for public app backend usage.

Rules:

- Must not be used for a public deployed endpoint.
- Backend may call MiMo only when `APP_ENV=local` or `APP_ENV=staging`.
- Backend must reject LLM calls when `APP_ENV=production`.
- Backend should expose a clear runtime warning: `subscription_dev mode is not allowed for public production traffic`.
- Optional extra guard: require an admin-only header or local-only network check for LLM calls.

### `disabled`

Purpose:

- Static/no-LLM deployment, provider outage, missing credentials, or compliance uncertainty.

Rules:

- Backend must not call MiMo.
- `/api/generate-prompt` always returns `mode: "fallback"`.
- Frontend continues using deterministic no-LLM generation.

Mode safety rule:

- If `LLM_CREDENTIAL_MODE` is missing or unknown, backend must default to `disabled`.
- If `APP_ENV=production` and `LLM_CREDENTIAL_MODE=subscription_dev`, backend must fail closed and never call MiMo.
- If `APP_ENV=production` and `LLM_CREDENTIAL_MODE=production_api` but `MIMO_API_KEY` is missing, backend must return fallback mode and log a safe configuration error.
- The provider key type should be documented in deployment notes, but never exposed to the frontend.

## Current State

The current frontend generates prompts in-browser through `window.FORGE.build(data)`.

The current Docker deployment has been simplified to static frontend only. To add LLM support safely, the backend service must be reintroduced for API calls, quota enforcement, and secret isolation.

Backend code already exists under `dnd-prompt-forge/backend/`, but it currently uses a simple FastAPI API and DeepSeek-style environment variable names. It should be refactored or replaced to support MiMo, multimodal input, and stronger security controls.

## Target Architecture

Use a backend-controlled hybrid generation flow:

1. Frontend submits form data and optional media metadata to backend.
2. Backend identifies the caller by IP, browser fingerprint hash, and signed cookie.
3. Backend checks hourly quota.
4. If quota remains, backend calls MiMo and returns LLM-enhanced prompt output.
5. If quota is exhausted, backend does not call MiMo and returns `mode: "fallback"` plus enough context for frontend deterministic generation.
6. Frontend renders either LLM output or local no-LLM output with a visible mode indicator.

High-level components:

- `frontend`: static UI, deterministic fallback generator, upload/media controls.
- `backend`: FastAPI service for auth, quota, MiMo calls, encryption, audit logging.
- `storage`: SQLite for local/dev or Postgres/Redis for production. Redis is preferred for rate-limit counters.
- `secret manager`: environment variables locally; production should use platform secret storage.

## Required API Endpoints

### `POST /api/session/bootstrap`

Purpose:

- Issue or refresh a signed anonymous session cookie.
- Return a short-lived CSRF token or request nonce.
- Return feature flags: `llm_enabled`, `image_enabled`, `video_enabled`, `quota_limit`, `quota_window_seconds`.

Security:

- Cookie must be `HttpOnly`, `Secure` in production, `SameSite=Lax` or `Strict`.
- Cookie value must be signed and tamper-evident.
- Do not expose provider API keys to the frontend.

### `POST /api/generate-prompt`

Purpose:

- Generate final prompt output using LLM when allowed.
- Fall back to deterministic mode when quota is exhausted or LLM is disabled.

Request fields:

- Existing prompt form fields: type, race, class, style, mood, description, target model, etc.
- `client_fingerprint`: browser fingerprint string generated client-side.
- `client_fingerprint_hash`: SHA-256 hash, preferred over raw fingerprint.
- Optional `media`: `{ kind: "image" | "video", source_type: "url" | "base64", mime_type, url, base64 }`.
- `fallback_prompt_preview`: optional deterministic output generated by frontend, used only for debugging and comparison.

Response fields:

- `mode`: `"llm"` or `"fallback"`.
- `quota`: `{ limit: 10, remaining, reset_at }`.
- `request_id`.
- `main_prompt`.
- `short_prompt`.
- `negative_prompt`.
- `style_notes`.
- `usage_tip`.
- `provider`: omit or redact internal details for fallback; safe label only for LLM.

### `GET /api/quota`

Purpose:

- Allow frontend to display remaining LLM calls without triggering an LLM request.

Response:

- `limit: 10`
- `remaining`
- `reset_at`
- `mode_available: "llm" | "fallback"`

## Quota Rule

User requirement:

Same IP or same browser fingerprint or same cookie, any one of these matching conditions, may call the LLM at most 10 times per hour.

Implementation:

- Track three independent hourly counters:
  - `quota:ip:{ip_hash}:{hour_bucket}`
  - `quota:fingerprint:{fingerprint_hash}:{hour_bucket}`
  - `quota:cookie:{session_id_hash}:{hour_bucket}`
- Before calling MiMo, load all three counters.
- If any counter is `>= 10`, deny LLM usage for this request and return fallback mode.
- If all are `< 10`, atomically increment all three counters before calling MiMo.
- If MiMo call fails due to provider outage, still record the attempt unless the failure happened before outbound call dispatch.

Storage:

- Redis is preferred because `INCR` + TTL is simple and race-safe.
- SQLite is acceptable for local development but needs transaction locking for concurrency.

IP handling:

- Use trusted proxy headers only when the reverse proxy is controlled by the app.
- Normalize IPv6.
- Hash IP before persistence.
- Do not trust arbitrary `X-Forwarded-For` unless the request comes from a trusted proxy.

Browser fingerprint:

- Use a privacy-conscious fingerprint from coarse browser properties.
- Hash fingerprint client-side and server-side.
- Do not persist raw fingerprint.
- Fingerprint is not a security boundary by itself; it is one quota signal.

Cookie:

- Use a server-issued signed anonymous ID.
- Rotate if tampered.
- Do not store personal identity.

## Security And Abuse Protection

### Secret Isolation

- MiMo API Key must exist only on the backend.
- Never expose MiMo credentials in frontend JS, HTML, Docker image layers, logs, or error responses.
- Environment variable names:
  - `MIMO_API_KEY`
  - `MIMO_BASE_URL`
  - `MIMO_MODEL=mimo-v2.5`
  - `MIMO_MAX_COMPLETION_TOKENS=1024`

### API Authentication

Because this is a public no-login app, use anonymous request authentication:

- Server-issued signed session cookie.
- CSRF token or request nonce required for mutating endpoints.
- Origin and Referer validation for browser requests.
- CORS allowlist for production domain only.
- Reject requests without a valid session cookie and nonce.

This does not make the API private, but it raises the cost of off-site extraction and automated reuse.

### Request Signing

Optional but recommended:

- Backend issues a short-lived nonce from `/api/session/bootstrap`.
- Frontend sends nonce with `/api/generate-prompt`.
- Backend validates one-time use or short TTL.
- Combine with session cookie; do not rely on client-side secrets.

### Encryption

- Use HTTPS only in production.
- Set HSTS at reverse proxy/CDN level.
- Encrypt provider API keys at rest if stored outside environment variables.
- If storing request logs, encrypt sensitive media metadata or avoid storing it.
- Hash IP, fingerprint, and cookie IDs before storing quota/audit records.

### Input Validation

- Validate JSON schema with strict Pydantic models.
- Enforce max text lengths for all form fields.
- Reject unsupported `media.kind`, `source_type`, and MIME types.
- Allow image MIME types only: `image/png`, `image/jpeg`, `image/webp`.
- Allow video MIME types only: `video/mp4`, `video/webm`, `video/quicktime`.
- Enforce documented provider size limits before sending to MiMo.
- For Base64 uploads, enforce a smaller product limit than provider maximum for cost control, for example:
  - image base64 max 10 MB product limit
  - video base64 max 30 MB product limit
- For URL media, validate scheme is `https`.
- Block private network targets and localhost to prevent SSRF if backend fetches URLs.
- Prefer passing user-provided public media URL directly to MiMo instead of server-side fetching.

### Output Safety

- System prompt must require:
  - DND/fantasy visual prompt generation only.
  - No copyrighted character names unless explicitly user supplied.
  - No explicit, hateful, extremist, or illegal content.
  - JSON-only response with strict keys.
- Backend must validate and sanitize provider response.
- If provider returns malformed JSON, fall back to deterministic generation.

### Logging

Log only:

- request_id
- timestamp
- mode
- quota identifiers as hashes
- media kind and size bucket
- provider model
- latency
- error category

Do not log:

- API keys
- raw fingerprint
- raw IP
- full Base64 media
- full generated prompt unless explicitly needed for debugging and gated by environment.

## Multimodal Prompt Flow

### Text Only

- Backend builds a structured MiMo prompt from the current form fields.
- MiMo returns JSON with main, short, negative, notes, and tip.
- Backend validates JSON and returns response.

### Image Analysis

- Frontend allows upload or URL input.
- Backend receives either a Base64 data URL or HTTPS media URL.
- Backend asks MiMo to analyze visible subject, style, composition, color, mood, and DND-relevant visual details.
- Backend converts analysis into prompt output.

### Video Analysis

- Frontend allows video upload or URL input.
- Backend receives either a Base64 data URL or HTTPS media URL.
- Backend asks MiMo to summarize key frames, subject, action, environment, mood, and DND-relevant visual details.
- Use `fps: 2` and `media_resolution: "default"` unless future testing shows cost/performance issues.
- Backend converts analysis into prompt output.

## Frontend Behavior

Required UI changes:

- Add LLM mode indicator: `LLM mode` / `No-LLM mode`.
- Add quota display: `x / 10 LLM calls remaining this hour`.
- Add optional media input area:
  - image upload
  - image URL
  - video upload
  - video URL
- Disable media upload when backend says multimodal is disabled.
- If backend returns fallback mode, show a subtle notice: "Hourly LLM quota reached. Generated locally without LLM."
- Keep the existing deterministic generator as the fallback and offline path.

Do not let frontend call MiMo directly.

## Docker Deployment Changes

Reintroduce backend service only when this scope is implemented:

- `frontend`: Nginx static frontend, proxies `/api/` to backend.
- `backend`: FastAPI service with MiMo credentials and quota control.
- Optional `redis`: quota store for production-like local testing.

Nginx should restore `/api/` reverse proxy only after backend endpoints exist.

Environment variables:

```text
FRONTEND_PORT=8081
BACKEND_PORT=8002
APP_ENV=production
LLM_CREDENTIAL_MODE=production_api
MIMO_API_KEY=
MIMO_BASE_URL=https://api.xiaomimimo.com/v1
MIMO_MODEL=mimo-v2.5
MIMO_MAX_COMPLETION_TOKENS=1024
LLM_QUOTA_LIMIT=10
LLM_QUOTA_WINDOW_SECONDS=3600
SESSION_COOKIE_SECRET=
CSRF_SECRET=
REDIS_URL=
```

## Acceptance Criteria

- Frontend can generate prompt with LLM when quota is available.
- Frontend automatically falls back to no-LLM generation after quota exhaustion.
- Backend enforces the 10/hour limit independently for IP, fingerprint, and cookie.
- If any one identifier exceeds 10/hour, no MiMo API call is made.
- MiMo API key is never exposed to frontend or logs.
- `/api/generate-prompt` rejects missing/invalid session cookie and nonce.
- CORS is limited to configured frontend origin in production.
- Media input supports image URL, image Base64, video URL, and video Base64 subject to size/MIME limits.
- Backend validates MiMo response shape before returning it.
- Docker deployment includes backend only after the API is implemented.
- Production deployment uses `LLM_CREDENTIAL_MODE=production_api` with credentials permitted for public app backend usage.
- `LLM_CREDENTIAL_MODE=subscription_dev` cannot call MiMo when `APP_ENV=production`.
- Missing or unknown `LLM_CREDENTIAL_MODE` fails closed to fallback/no-LLM mode.

## Implementation Phases

### Phase 1: Backend Security Skeleton

- Add FastAPI session bootstrap.
- Add signed cookie and nonce validation.
- Add quota service with SQLite for local development.
- Add deterministic fallback API response.
- Add `APP_ENV` and `LLM_CREDENTIAL_MODE` checks that fail closed.

### Phase 2: MiMo Text LLM

- Add MiMo OpenAI-compatible client.
- Add structured prompt contract.
- Add JSON validation and fallback-on-error.
- Allow MiMo calls only when credential mode policy permits it.

### Phase 3: Multimodal

- Add image input support.
- Add video input support.
- Add media MIME/size validation.
- Add UI controls.

### Phase 4: Production Hardening

- Add Redis quota backend.
- Add trusted proxy IP handling.
- Add CORS/origin hardening.
- Add Docker backend and optional Redis services.
- Add deployment secret checklist.

### Phase 5: Verification

- Unit tests for quota logic.
- API tests for auth/nonce failures.
- API tests for fallback after 10 calls.
- API tests confirming no provider call is made after quota exhaustion.
- Browser test for LLM mode and fallback mode.
- Security review for logs, headers, cookies, and secrets.

## Open Questions

- Confirm which Xiaomi/MiMo credential type is permitted for public app backend usage. Use that with `production_api`; keep Token Plan or subscription-style credentials in `subscription_dev` only unless Xiaomi explicitly permits production app usage.
- Decide production quota store: Redis recommended; SQLite acceptable only for small single-instance deployment.
- Decide whether media uploads are kept in memory only or temporarily stored.
- Decide product-side media limits below provider maximum to control cost.
- Decide exact production domain for CORS and cookie settings.
