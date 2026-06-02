# DND Prompt Forge -- Value Review: LLM Multimodal Security

**Review Date**: 2026-06-02
**Reviewer**: Gemini Cognitive Engine v4.0
**Source Documents**:
- `/workspace/docs/scope-change/20260602-llm-multimodal-security.md`
- `/workspace/dnd-prompt-forge/docs/requirements.md`
- `/workspace/dnd-prompt-forge/backend/main.py` (current backend)

---

## 1. Essence Deconstruction

### What is the fundamental problem, stripped of all frameworks?

A free SEO landing page uses a browser-side template engine to concatenate D&D character attributes into English AI image prompts. The templates are formulaic -- they always produce "a {gender} {race} {class}, painterly fantasy illustration, heroic mood." After 3-4 uses, the output pattern becomes visible and repetitive.

The proposal asks: should we add a server-side LLM to generate more varied, creative, contextually-aware prompts, while keeping the template engine as fallback?

### Physical analogy

You own a workshop with a stamping machine that produces decent D&D prompt cards. Someone proposes hiring a professional calligrapher who charges per-word to hand-write custom cards. You can only afford 10 calligrapher jobs per hour. When the calligrapher is booked or unavailable, customers get the stamped version.

The question: does the calligrapher add enough value per card to justify:
- Building a scheduling system (quota tracking)
- Installing a security gate (session/nonce/CORS)
- Managing the calligrapher's contract and credentials (MiMo API key isolation)
- Expanding the workshop to house the calligrapher (Redis, additional containers)

### What already exists

The current `backend/main.py` (470 lines) already contains:
- A functional LLM integration (`call_deepseek()`) -- operational, just not deployed
- A mature deterministic fallback engine (`build_fallback_prompt()`) with per-type prompt structures, style/mood descriptors, model-specific suffixes, and type-specific negative prompts
- SQLite persistence for prompt_requests, feedback_events, and self-correcting memory_rules
- CORS open to all origins (no authentication)

The proposal would:
- Migrate from DeepSeek to MiMo (no stated reason for the switch)
- Layer session management, CSRF protection, 3-dimensional quota tracking, credential mode system, media validation, and multimodal architecture on top
- Expand from 1 Docker container to 3 (Nginx + FastAPI + Redis)

### The irreducible minimum

The core value proposition is: **LLM-generated prompts are higher quality than template-generated prompts.** Everything else (multimodal, credential modes, 3D quota, signed cookies) is scaffolding to deliver that value safely and economically. But the scaffolding represents ~70% of the proposed implementation effort.

---

## 2. Core Contradictions

### Contradiction 1: MVP simplicity vs. production security

The project charter calls it a "1-2 day MVP experiment." The scope document proposes 5 implementation phases covering session management, CSRF nonces, signed cookies, 3-dimensional quota tracking, credential mode state machines, Redis deployment, multimodal architecture, and production hardening.

These two premises cannot both be true. Either:
- (A) This is an MVP, and the security skeleton should be the simplest thing that prevents cost overrun and key leakage, OR
- (B) This is a production SaaS product, and the proposed security architecture is appropriate.

The document attempts to have it both ways, calling it an MVP while proposing SaaS-grade security.

### Contradiction 2: LLM quality vs. two-tier user experience

The proposal requires a visible "LLM mode" / "No-LLM mode" indicator. When quota is exhausted, users see: "Hourly LLM quota reached. Generated locally without LLM."

This creates a perverse incentive: the very existence of LLM mode degrades the perceived quality of the fallback. A user who only ever saw deterministic generation would perceive it as "the product." After being told they're getting the "inferior version," the same output feels like a downgrade.

The original project premise was that deterministic generation IS the product. The LLM addition risks turning the core product into a "sorry, downgraded" experience.

### Contradiction 3: Anonymous users vs. sophisticated tracking

The proposal insists on "completely anonymous, no personal data." But then implements:
- Browser fingerprinting (coarse but still privacy-invasive)
- Signed session cookies
- IP hashing with hourly bucket tracking

Fingerprinting for quota purposes is philosophically at odds with the "completely anonymous" promise. Browser fingerprinting is increasingly regulated (GDPR, ePrivacy). For a free SEO tool, this creates compliance risk disproportionate to the benefit.

### Contradiction 4: Phase 3 premature architecture

Phase 3 (multimodal: image/video analysis) is listed as "reserved interfaces only, 501 placeholder" in the PRD, yet the scope document builds the entire infrastructure scaffolding with Phase 3 in mind:
- Media metadata fields in the request schema
- MIME type validation for video/quicktime and video/webm
- Base64 size limits for images (10MB) and videos (30MB)
- SSRF prevention for URL media
- Per-frame video analysis parameters (fps: 2, media_resolution)

This is architecture for a feature with zero evidence of user demand. D&D prompt generation is fundamentally a text-to-text task (character attributes to prompt text). The original PRD's pain points are all about translating character concepts into prompt language -- none involve reference images or videos.

---

## 3. System Impact Analysis

### Chain 1: Frontend rendering model change

```
BEFORE: Static HTML loads -> user fills form -> window.FORGE.build() -> instant result
AFTER:  Static HTML loads -> user fills form -> POST /api/generate-prompt -> wait 2-10s -> result or fallback
```

Impact:
- All generator pages (~10-15 pages) need async API integration
- JavaScript bundle size increases
- Core Web Vitals: FCP unaffected, but LCP may degrade (content populated after API response)
- SEO risk: Googlebot may not execute JavaScript to see generated content. If it does, the 2-10s API latency hurts crawl budget.
- The `sitemap.xml` lists specific long-tail pages (e.g., `/tiefling-warlock-prompt-generator`) that were previously pre-renderable static HTML. With API-dependent generation, these pages lose their crawlable content advantage.

### Chain 2: Backend complexity expansion

```
BEFORE: FastAPI (470 lines) -> SQLite -> LLM or fallback -> response
AFTER:  FastAPI (2000+ lines) -> session middleware -> quota service -> credential resolver -> CSRF validator -> MiMo client -> JSON validator -> response
        + Redis/SQLite for quota counters
        + Cookie signing infrastructure
        + Media validation pipeline
```

Impact:
- Backend grows 3-5x in code surface
- New failure modes at every middleware layer
- Testing surface expands dramatically (auth, quota, media, credential modes, fallback -- all combinations)
- The existing `memory_rules` self-correction system must coexist with the new security layer without interference

### Chain 3: Infrastructure topology change

```
BEFORE: 1 container (Nginx static)
AFTER:  3 containers (Nginx + FastAPI + Redis)
```

Impact:
- Docker Compose configuration doubles in complexity
- Production requires monitoring 3 services, not 1
- Redis becomes a new single point of failure for the LLM path
- Redis failure mode dilemma: fail open (risk cost overrun when quota counter lost) or fail closed (LLM unusable, everything falls back to deterministic)? The scope document does not resolve this.

### Chain 4: Deployment simplicity loss

```
BEFORE: "docker compose up --build -d" -> 1 service at localhost:8081
AFTER:  "docker compose up --build -d" -> 3 services, requirement to set 12+ environment variables
```

The current `deploy/README.md` is 44 lines. The new deployment README will need to document:
- MiMo credential acquisition
- Credential mode selection and its restrictions
- Session cookie secret generation
- CSRF secret generation
- Redis configuration (or SQLite fallback caveats)
- Trusted proxy configuration for correct IP detection

This shifts the project from "anyone can deploy this" to "requires understanding of production security configuration."

---

## 4. Risk Identification

### HIGH: MiMo credential compliance uncertainty

The scope document explicitly flags: "Token Plan subscription docs prohibit API-call usage in custom application backends or other obvious non-coding scenarios." The mitigation is to use `production_api` mode with "ordinary API billing credentials."

However, the document does not confirm:
- Whether MiMo/Xiaomi offers "ordinary API billing credentials" distinct from Token Plan
- What the pricing model is for such credentials
- Whether they permit this specific use case (prompt generation for public web app)

**Risk**: Build the entire system, then discover MiMo's terms of service prohibit this usage, forcing either a provider switch or compliance violation.

### HIGH: SEO regression from API-dependent content

The current architecture's SEO advantage is speed: static HTML, instant TTFB, immediately crawlable content. Adding an async API dependency for the core value proposition (generated prompts) could:
- Delay LCP by 2-10 seconds
- Prevent Googlebot from seeing generated content
- Make long-tail pages (tiefling-warlock, elf-ranger, etc.) less indexable

The PRD mentions "ensure SSR or pre-rendering" but the current architecture (static Nginx) cannot do SSR without adding a Node.js server. This is a material gap.

### MEDIUM: Quota bypass via cookie/fingerprint rotation

The 3-dimensional tracking (IP + fingerprint + cookie) is designed to make quota evasion harder. But in practice:
- Clearing cookies resets the cookie dimension, granting fresh quota on first session bootstrap
- Using incognito mode resets both fingerprint and cookie
- VPN rotation resets IP

The quota system adds significant complexity but can be trivially bypassed by anyone who knows how. For a free tool, the cost of bypass is zero (no paid tier to protect), so the incentive to bypass is low. This means the complex 3D tracking adds little practical protection.

### MEDIUM: "Quota nightmare" UX

A user opens 3 tabs with different characters. Tab 1 makes 4 requests, Tab 2 makes 4, Tab 3 makes 4. With 3-dimensional tracking and browser fingerprinting varying per tab context, the user might get inconsistent quota states across tabs. Some tabs show "remaining: 2" while others show "remaining: 10." This confuses users and generates support burden.

### MEDIUM: The multimodal cost trap

If Phase 3 is eventually implemented, image/video analysis calls cost significantly more than text-only generation. The 10/hour quota designed for text generation would need recalibration. A single video analysis could cost 10-50x a text call. Without cost modeling, this is a budget risk.

### LOW: Provider lock-in disguised as "generic"

The scope document says "Keep the provider configuration generic." But the implementation:
- Hardcodes `MIMO_*` environment variable names
- References MiMo-specific model names (`mimo-v2.5`, `mimo-v2-omni`)
- References MiMo-specific API docs for image/video understanding parameters

True provider-generic design would use names like `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL` and handle provider-specific request formatting through an adapter pattern. As written, "generic" is aspirational but not architecturally realized.

---

## 5. Simpler Proposal

The core insight (LLM-enhanced prompts with deterministic fallback) has genuine value. The implementation should be reduced to its irreducible minimum:

### Simplified Architecture

| Layer | Current Proposal | Simplified |
|-------|-----------------|------------|
| LLM Provider | MiMo (migration from DeepSeek) | Keep DeepSeek (already integrated, working) |
| Quota | 3 dimensions (IP + fingerprint + cookie) via Redis | 1 dimension (IP only), in-memory counter with SQLite persistence |
| Auth | Signed session cookies + CSRF nonces + origin validation | CORS restricted to production domain + simple origin check |
| Credential Management | 3-mode state machine (production_api / subscription_dev / disabled) | Single env var `LLM_API_KEY` -- if set, use LLM; if not, fallback |
| Multimodal | Image/video analysis with MIME validation, SSRF prevention, Base64 limits | Deferred entirely until user demand is proven |
| Infrastructure | 3 containers (Nginx + FastAPI + Redis) | 2 containers (Nginx + FastAPI), no Redis |
| Deployment | 12+ environment variables | 4 environment variables (API_KEY, BASE_URL, MODEL, APP_ENV) |
| Frontend | Async API calls + loading states + quota display + mode indicator | Async API calls + loading states only; no quota display, no mode stigma |

### Phases

**Phase 1 (2-3 days)**: Deploy existing DeepSeek integration
- Add IP-based rate limiting (in-memory counter, periodic SQLite flush)
- Restrict CORS to configured origin in production
- Keep existing fallback when API key is missing or rate limited
- Frontend: call `/api/generate-prompt`, fall back to `window.FORGE.build()` on error
- Docker Compose: add backend service to existing configuration

**Phase 2 (1 day)**: Polish
- Loading states, error messages
- `/api/quota` endpoint (read-only, no Redis needed -- query in-memory counter)
- Deployment documentation

**Phase 3 (future, data-driven)**: Re-evaluate based on actual usage
- If users consistently hit quota ceiling, consider increasing or adding fingerprint dimension
- If users request image-based prompt generation, add multimodal then
- If DeepSeek cost/quality becomes an issue, evaluate provider migration then

### What the simplified approach sacrifices

- **Multimodal support**: No image/video input. But this is speculative demand with zero evidence.
- **Browser fingerprinting**: Quota is IP-only, easier to bypass. But the cost exposure is capped at DeepSeek's per-call pricing, and a bypasser still only gets 10 more calls per IP change.
- **Session cookies/CSRF**: Less protection against automated scraping. But for a free tool with no user data, the attack incentive is near-zero.
- **MiMo migration**: Stay on DeepSeek. If there is a specific reason DeepSeek is unsuitable, the simplified approach preserves the option to migrate later.
- **Redis**: In-memory counters reset on restart. Acceptable for MVP; add Redis when single-VPS limitations become real.

### What the simplified approach preserves

- **LLM-enhanced prompt quality**: The core value proposition is intact.
- **Deterministic fallback**: The existing `build_fallback_prompt()` is fully functional and deployed.
- **Cost control**: IP-based 10/hour limit prevents runaway API bills.
- **Key isolation**: API key in backend environment variable only, never exposed to frontend.
- **Fast time-to-market**: ~3 days vs. ~2-3 weeks for the full proposal.

---

## 6. Summary

The proposal correctly identifies a real opportunity: LLM-generated prompts are higher quality than deterministic templates, and having both paths (LLM primary, template fallback) is architecturally sound.

However, the implementation plan is mismatched to the project's scope and stage. A free, anonymous SEO landing page designed as a 1-2 day MVP does not need signed session cookies, CSRF nonces, 3-dimensional quota tracking, a 3-mode credential state machine, Redis, or multimodal architecture scaffolding. These are features of a paid SaaS product, not a free SEO experiment.

The simpler path -- deploy the already-working DeepSeek integration with basic IP rate limiting, keep CORS restricted, add loading states to the frontend -- delivers 80% of the value at 20% of the complexity and time investment.

Multimodal, advanced quota, and provider migration can be re-evaluated when user data supports them.

---

VERDICT: SIMPLER_PROPOSAL
