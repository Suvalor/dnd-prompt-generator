# DND Prompt Forge — Frontend-Backend Integration Design Spec

> Version: 1.0 | Date: 2026-06-02 | Author: product-designer | Status: DRAFT

## 1. Design System Audit Summary

**Current stack**: React 18 (Babel in-browser), no build tools, Lucide icons, custom CSS with CSS custom properties.

**Design language**: "Practical fantasy workshop" -- warm parchment base (#F4EEDF), brass primary (#9A6E22), crimson/emerald accents, Cormorant Garamond serif for display, Manrope sans for body, JetBrains Mono for code.

**Existing component primitives** (from `primitives.jsx`): Icon, Button, Field, Segmented, Select, CopyButton, Collapse, ToastHost/useToast.

**Existing output sub-views** (from `generator.jsx`): EmptyState, LoadingState, ErrorState, SuccessState, Feedback, PromptBlock.

**Key constraint**: No Tailwind, no component library primitives (Base UI / Radix / React Aria). All styling is custom CSS with CSS custom properties.

## 2. Business Logic Model

### 2.1 Data Constraints

| Field | Source | Constraint | Validation |
|-------|--------|------------|------------|
| `csrf_token` | bootstrap response | Non-empty string, stored in memory | Frontend: check truthy before API call |
| `features.llm_enabled` | bootstrap response | boolean | Controls whether API call is attempted |
| `features.quota_limit` | bootstrap response | integer >= 0 | Display baseline |
| `mode` | generate response | `"llm"` or `"fallback"` | Drives mode badge |
| `quota.remaining` | generate response | integer >= 0 | Drives quota display |
| `quota.limit` | generate response | integer >= 0 | Drives quota display |
| `quota.reset_at` | generate response | ISO 8601 datetime string | Not displayed in v1 (reserved) |

### 2.2 Business Rules

1. **Bootstrap-first**: No generate call until bootstrap completes. If bootstrap fails, all generate calls use local `FORGE.build()` with mode="local".
2. **CSRF gate**: Every `POST /api/generate-prompt` must include `x-csrf-token` header. Missing token = 403 = fallback to local.
3. **Mode determination** (priority order):
   - `mode=llm`: Backend returned LLM-generated prompt. Display LLM badge.
   - `mode=fallback`: Backend returned deterministic prompt (quota exceeded OR LLM failed). Display Fallback badge.
   - `mode=local`: Backend unreachable / network error / bootstrap failed. Frontend used `FORGE.build()`. Display Local badge.
4. **Quota display**: Show `remaining / limit` after every successful generate. When `remaining=0`, show quota-exhausted notice.
5. **Quota reset**: Hourly window. No countdown timer in v1.
6. **Fingerprint**: Best-effort SHA-256 via `crypto.subtle`. Failure = send empty string. Backend tolerates null.

### 2.3 Frontend vs Backend Logic Boundary

| Logic | Owner | Rationale |
|-------|-------|-----------|
| Session bootstrap call | Frontend | Triggers on mount |
| CSRF token storage | Frontend (memory) | Never persisted to localStorage (security) |
| Field mapping (form -> API) | Frontend | `klass` -> `class_role`, `type` -> `output_type`, etc. |
| Fingerprint hash generation | Frontend | Uses browser crypto API |
| Fallback to FORGE.build() | Frontend | Only on network error / backend unreachable |
| Quota check | Backend | Authoritative; frontend only displays result |
| Mode determination (llm/fallback) | Backend | Authoritative; frontend only displays result |
| Mode determination (local) | Frontend | Inferred from network failure |
| Minimum loading duration | Frontend | Prevents flash; 600ms floor |
| Quota exhausted notice | Frontend | Display logic based on backend response |

---

## 3. Full-Path Business Flow

```
Page Mount -> Bootstrap /api/session/bootstrap
  -> Success: Store csrf_token + features in memory
  -> Network Error: Mark apiAvailable=false

User fills form -> Click Generate
  -> IF apiAvailable=false: Local FORGE.build() -> mode=local
  -> IF features.llm_enabled=false: Local FORGE.build() -> mode=local
  -> IF sessionReady: POST /api/generate-prompt with CSRF
    -> HTTP 200 mode=llm: Display LLM result + LLM badge + quota
    -> HTTP 200 mode=fallback + remaining>0: Display fallback + Fallback badge + quota
    -> HTTP 200 mode=fallback + remaining=0: Display fallback + Fallback badge + quota=0 crimson + exhausted banner
    -> HTTP 403: CSRF invalid -> re-bootstrap then retry once
    -> Network Error: Retry once (1s delay) -> if still fails -> Local FORGE.build() -> mode=local
    -> Timeout (25s): Local FORGE.build() -> mode=local
```

### Exception Paths

1. **Bootstrap timeout**: 5s timeout. On failure, set `apiAvailable=false`, continue with local-only mode. No error banner.
2. **CSRF 403 on generate**: Attempt one re-bootstrap. If re-bootstrap succeeds, retry generate. If re-bootstrap fails, fallback to local.
3. **Network error on generate**: One automatic retry (1s delay). If retry fails, fallback to local. No error banner.
4. **Persistent backend failure** (3+ consecutive failures): Show subtle info banner: "Using offline mode -- prompts are generated locally from templates." Dismissible, does not re-appear for session.
5. **crypto.subtle unavailable** (non-HTTPS): Send `client_fingerprint_hash: ""`. Backend handles null/empty gracefully.

---

## 4. Interaction Specification

### 4.1 Mode Badge

**Component**: Inline badge in `out-head` area of SuccessState, adjacent to existing "Ready to copy" pill.

**Visual spec**:
- Uses existing `.pill` base class
- Three variants:
  - `.pill.llm` -- emerald-soft background, emerald-fg text, emerald dot. Text: "AI Enhanced"
  - `.pill.fallback` -- brass-soft background, brass-fg text, brass dot. Text: "Standard"
  - `.pill.local` -- inset background, ink-3 text, no dot. Text: "Offline"
- Font: `var(--t-label)` (existing pill style)
- Size: same as existing `.pill.ok` (5px 10px padding, r-full radius)

**Data binding**: `result.mode` (string: "llm" | "fallback" | "local")

**State matrix**:

| State | Visual | Text | Dot |
|-------|--------|------|-----|
| LLM | emerald-soft bg, emerald-fg text | AI Enhanced | emerald dot |
| Fallback | brass-soft bg, brass-fg text | Standard | brass dot |
| Local | inset bg, ink-3 text | Offline | none |

**Accessibility**: `aria-label` on the pill span: e.g. `aria-label="Generation mode: AI Enhanced"`

### 4.2 Quota Display

**Component**: Inline text in `out-meta` area of SuccessState, appended after existing meta items.

**Visual spec**:
- Uses existing `.out-meta` styling (t-label font, ink-3 color, mono family)
- Format: `<b>Quota</b> {remaining} / {limit}`
- Uses `tabular-nums` (already on `.out-meta` via `--t-mono`)
- When `remaining=0`: text color changes to `var(--crimson-fg)`

**State matrix**:

| Condition | Color | Text | aria-label |
|-----------|-------|------|------------|
| remaining > 2 | var(--ink-3) | `<b>Quota</b> 7 / 10` | "Quota: 7 of 10 remaining" |
| 1 <= remaining <= 2 | var(--brass-fg) | `<b>Quota</b> 2 / 10` | "Quota: 2 of 10 remaining" |
| remaining = 0 | var(--crimson-fg) | `<b>Quota</b> 0 / 10` | "Quota exhausted: 0 of 10 remaining" |
| mode=local (no quota) | N/A | Not displayed | N/A |

### 4.3 Quota Exhausted Notice

**Component**: A `.banner` inserted between `out-head` and `full-copy` in SuccessState, only when `mode=fallback` AND `quota.remaining=0`.

**Visual spec**:
- Uses existing `.banner` base class with a new variant `.banner.warn`
- Background: `var(--brass-soft)`, border: `1px solid color-mix(in oklab, var(--brass) 30%, transparent)`
- Text color: `var(--brass-fg)`
- Icon: Lucide `alert-circle` (size 17)
- Text: "AI-enhanced prompts have reached the hourly limit. Using standard generation. Limit resets each hour."

### 4.4 Loading State Enhancement

**New behavior**:
1. Set `status='loading'` immediately
2. Call API (or local fallback)
3. Apply minimum display duration: `Math.max(600, actualDuration)` -- if API responds in 200ms, wait until 600ms total to prevent flash
4. Maximum wait: API timeout at 25s
5. On timeout: fallback to local

### 4.5 Offline Mode Info Banner

**Component**: A `.banner.warn` shown at the top of the output panel when the frontend has detected that the backend is unavailable.

**Trigger**: After 3+ consecutive API failures (including retries), OR bootstrap failure.

**Text**: "Using offline mode -- prompts are generated locally from templates."

**Behavior**:
- Persists for the session (stored in state as `offlineMode=true`)
- Not dismissible
- Does not block generation
- If a subsequent API call succeeds, `offlineMode` resets to false and banner disappears

**Accessibility**: `role="status"` on the banner div for screen reader announcement.

---

## 5. UI State Matrix -- Generate Button Click

| From State | Event | To State | Mode | UI Elements |
|------------|-------|----------|------|-------------|
| empty | Click Generate | loading | - | Skeleton, button disabled |
| loading | API success, mode=llm | success | llm | LLM badge, quota display, result |
| loading | API success, mode=fallback, remaining>0 | success | fallback | Fallback badge, quota display, result |
| loading | API success, mode=fallback, remaining=0 | success | fallback | Fallback badge, quota=0 crimson, exhausted banner, result |
| loading | API 403, re-bootstrap success, retry success | success | llm/fallback | Per mode above |
| loading | API 403, re-bootstrap success, retry fail | success | local | Local badge, no quota, offline banner (if 3+ fails) |
| loading | API network error, retry success | success | llm/fallback | Per mode above |
| loading | API network error, retry fail | success | local | Local badge, no quota, offline banner (if 3+ fails) |
| loading | API timeout (25s) | success | local | Local badge, no quota, offline banner |
| loading | apiAvailable=false (bootstrap failed) | success | local | Local badge, no quota, offline banner |
| success | Click Regenerate | loading | - | Skeleton, button disabled |
| success | Click "Not useful" | success (feedback phase) | unchanged | Feedback form appears below result |

---

## 6. CSS Additions

All new styles use existing CSS custom properties. No new color tokens. No new fonts. No gradients.

```css
/* === Mode Badge Pills === */
.pill.llm{color:var(--emerald-fg);background:var(--emerald-soft);}
.pill.llm .dot{width:6px;height:6px;border-radius:999px;background:var(--emerald);}
.pill.fallback{color:var(--brass-fg);background:var(--brass-soft);}
.pill.fallback .dot{width:6px;height:6px;border-radius:999px;background:var(--brass);}
.pill.local{color:var(--ink-3);background:var(--inset);}

/* === Quota Display === */
.out-meta .quota-low{color:var(--brass-fg);}
.out-meta .quota-exhausted{color:var(--crimson-fg);}

/* === Banner Warn (brass-toned informational) === */
.banner.warn{background:var(--brass-soft);color:var(--brass-fg);
  border:1px solid color-mix(in oklab,var(--brass) 30%,transparent);}
```

---

## 7. Component Change List

### 7.1 New File: `js/api-client.jsx`

Must be loaded BEFORE `generator.jsx` in `index.html`.

Exports to `window`:
- `window.ApiClient.bootstrap()` -- returns `{ csrf_token, features }` or throws
- `window.ApiClient.generatePrompt(form, csrfToken, fingerprintHash)` -- returns API response or throws
- `window.ApiClient.generateFingerprint()` -- returns SHA-256 hash string or ""

### 7.2 Modified: `js/generator.jsx`

**SuccessState** changes:
1. Accept new props: `mode`, `quota` (object with `remaining`, `limit`)
2. Add Mode Badge before existing "Ready to copy" pill in `out-head`
3. Add Quota Display in `out-meta` (after existing meta spans)
4. Add Quota Exhausted Banner between `out-head` and `full-copy` when conditions met
5. Add Offline Mode Banner at top of output when `offlineMode` state is true

**Generator** changes:
1. New state: `apiState` with shape `{ csrfToken: string|null, features: object|null, apiAvailable: boolean, offlineMode: boolean, consecutiveFailures: number }`
2. New state: `quota` with shape `{ remaining: number, limit: number }`
3. New state: `mode` (string: "llm" | "fallback" | "local")
4. `runGenerate` rewritten: API call with retry + fallback logic
5. Pass `mode`, `quota`, `offlineMode` to SuccessState

### 7.3 Modified: `js/app.jsx`

1. On mount: call `window.ApiClient.bootstrap()`, store result in a ref/state
2. Pass bootstrap result down to Generator via new prop: `apiConfig`

### 7.4 Modified: `index.html`

1. Add `<script type="text/babel" src="js/api-client.jsx"></script>` BEFORE the generator.jsx script tag

### 7.5 Modified: `css/style.css`

1. Add the CSS additions from Section 6 above

---

## 8. Accessibility Checklist

| Element | ARIA Attribute | Value |
|---------|---------------|-------|
| Mode Badge (pill) | `aria-label` | "Generation mode: {AI Enhanced / Standard / Offline}" |
| Quota Display span | `aria-label` | "Quota: {n} of {limit} remaining" or "Quota exhausted: 0 of {limit} remaining" |
| Quota Exhausted Banner | (inherits from parent `aria-live="polite"`) | N/A |
| Offline Mode Banner | `role="status"` | N/A |
| LoadingState | `aria-busy="true"`, `aria-live="polite"` | Already present |
| Generate button (loading) | `aria-disabled="true"` (via disabled attr) | Already handled |

---

## 9. Architect Focus Points

The following items require Architect confirmation or backend coordination:

1. **API response field names**: The design assumes the backend `POST /api/generate-prompt` returns `{ mode, request_id, quota: { limit, remaining, reset_at }, main_prompt, short_prompt, negative_prompt, style_notes, usage_tip }`. Confirm these match the actual Pydantic model.

2. **Bootstrap response field names**: Assumes `{ csrf_token, features: { llm_enabled, image_enabled, video_enabled, quota_limit, quota_window_seconds } }`. Confirm match.

3. **CSRF header name**: Assumes `x-csrf-token`. Confirm this matches the CSRF middleware expectation.

4. **Session cookie name**: Assumes `session_id`. Confirm this matches `response.set_cookie(key="session_id", ...)` in session router.

5. **API timeout recommendation**: Frontend will use 25s timeout for generate-prompt. Backend LLM timeout is 20-40s per requirements. Is 25s sufficient, or should frontend match the upper bound?

6. **Fingerprint hash format**: Frontend will send raw SHA-256 hex string (64 chars). Backend `client_fingerprint_hash` field accepts Optional[str]. Confirm no length/format constraint.

7. **CORS configuration**: Frontend fetch needs `credentials: 'include'` for cookie transmission. Confirm backend CORS middleware allows credentials and the correct origin.
