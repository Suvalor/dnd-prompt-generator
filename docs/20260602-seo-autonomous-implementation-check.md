# SEO Autonomous Static Content System Implementation Check

Date: 2026-06-02

Checked scope document:

```text
docs/scope-change/20260602-seo-autonomous-static-content-system.md
```

## Verdict

Not implemented.

The scope document has been restored and is present in the repository, but the codebase does not currently implement the autonomous SEO static content system described there.

Current state is closer to:

- Existing static frontend baseline.
- Existing manual `sitemap.xml`, `robots.txt`, core page canonical tags, and homepage FAQ/content blocks.
- No daily SEO automation pipeline.
- No Astro/SSG SEO content layer.
- No generated long-tail static pages.
- No keyword trend ingestion.
- No LLM-based SEO decision/generation workflow.
- No SEO page registry or failure registry.

## Acceptance Matrix

| Requirement from scope document | Status | Evidence |
| --- | --- | --- |
| Frontend should no longer be deployed to Docker | Failed | `docker-compose.yml` still defines a `frontend` service and builds `frontend/Dockerfile`. |
| Backend code can remain | Passed | `dnd-prompt-forge/backend/main.py` remains. |
| Static SEO site layer should use Astro | Failed | No `astro.config.*`, no Astro package setup, no `src/content/seo-pages`. |
| Daily midnight SEO workflow | Failed | No `.github/workflows` directory or scheduler found. |
| Google Trends keyword discovery | Failed | No SEO worker/script/API client found for trend ingestion. |
| Search Console data integration | Failed | No Search Console API integration found. |
| LLM Decision Contract for SEO candidates | Failed | No SEO LLM decision schema, candidate selector, or generation module found. |
| LLM cost and rate limiting for SEO generation | Failed | No SEO quota/cost tracking implementation found. |
| `frontend/data/seo-pages.json` registry | Failed | File/directory missing. |
| `frontend/data/seo-failures.json` failure registry | Failed | File/directory missing. |
| `docs/seo-runs/YYYYMMDD-*.md` run reports | Failed | `docs/seo-runs/` missing. |
| Generate or update static long-tail SEO pages | Failed | Sitemap lists long-tail URLs, but no matching static HTML files exist for them. |
| Generator prefill from SEO pages | Failed | No `generator-prefill` handling found in frontend app code. |
| Sitemap automation | Failed | `sitemap.xml` exists, but no registry-driven updater found. |
| Canonical automation | Failed | Core pages have manual canonicals, but no generated-page canonical workflow exists. |
| Internal-link automation | Failed | Existing links are static/manual only; no SEO registry-driven link updater found. |
| FAQ automation and FAQ JSON-LD validation | Failed | Existing FAQ exists on homepage, but no generation/validation pipeline found. |
| Content drift detection | Failed | No `content_fingerprint`, similarity checks, or threshold calibration implementation found. |
| Quality gates | Failed | No automated quality gates for generated SEO pages found. |
| Rollback-ready daily commit workflow | Failed | No CI workflow or daily commit process found. |
| Phase 1 MVP output | Failed | No one-page-per-day generator, run report, registry, or failure handling exists. |
| Existing SEO baseline | Partially passed | Homepage, legal pages, robots, sitemap, and visible FAQ/content sections exist. |

## Detailed Findings

### 1. Docker deployment conflicts with the scope

The scope requires frontend not to deploy through Docker. Current `docker-compose.yml` still deploys both backend and frontend:

```text
services:
  backend:
    ...
  frontend:
    build:
      context: ./dnd-prompt-forge
      dockerfile: frontend/Dockerfile
    depends_on:
      backend:
        condition: service_healthy
```

`docker compose config` also confirms:

```text
services:
  backend:
    ...
  frontend:
    build:
      dockerfile: frontend/Dockerfile
    depends_on:
      backend:
        condition: service_healthy
```

### 2. Astro/SSG layer is absent

Expected by the scope:

- Astro static output.
- SEO content collections.
- Generated SEO page templates.
- Astro migration path/triggers.

Current evidence:

- No `astro.config.*`.
- No `package.json` for Astro build.
- No `src/content/seo-pages`.
- No generated static SEO page directory.

### 3. SEO automation pipeline is absent

Expected by the scope:

- Daily run at 00:00.
- Keyword discovery from Google Trends or fallback sources.
- Search Console signal ingestion.
- LLM candidate decision.
- Static content generation.
- Quality gates.
- Daily report and commit.

Current evidence:

- No `.github/workflows`.
- No SEO scripts directory.
- No keyword candidate files.
- No Search Console integration.
- No trend ingestion implementation.
- No LLM SEO decision contract implementation.
- No `docs/seo-runs/` output directory.

### 4. Long-tail sitemap URLs are not real static pages

The current sitemap has long-tail URLs, but most do not map to static HTML files.

Passed static URL check:

```text
/
/about
/privacy
/terms
/contact
```

Missing static HTML:

```text
/dnd-character-prompt-generator
/dnd-token-prompt-generator
/dnd-monster-prompt-generator
/dnd-npc-prompt-generator
/dnd-scene-prompt-generator
/fantasy-character-prompt-generator
/tiefling-warlock-prompt-generator
/elf-ranger-prompt-generator
/dragonborn-paladin-token-prompt
/dnd-tavern-scene-prompt
/dnd-villain-prompt-generator
/dnd-cleric-portrait-prompt
/dnd-rogue-character-prompt
/dnd-wizard-character-prompt
/dnd-bard-character-prompt
/dnd-druid-character-prompt
```

This means the sitemap advertises SEO URLs that are currently served by the SPA fallback, not by distinct crawlable static content pages.

### 5. Generator prefill interaction is absent

Expected by the scope:

- SEO pages carry generator prefill data.
- Frontend reads `#generator-prefill`.
- Tool opens with relevant prompt type and values.

Current frontend routing in `dnd-prompt-forge/frontend/js/app.jsx` only supports:

- home
- about
- privacy
- terms
- contact
- type shortcuts such as character/token/monster/scene/npc

No `generator-prefill` handling was found.

### 6. Backend exists, but it is not the SEO automation backend

Current backend is still a prompt generation API using DeepSeek-style environment variables:

```text
DEEPSEEK_API_KEY
DEEPSEEK_BASE_URL
DEEPSEEK_MODEL
```

It has SQLite tables for:

- `prompt_requests`
- `feedback_events`
- `memory_rules`

That partially overlaps the scope's idea of feedback/memory data existing, but there is no bridge from those tables into the SEO generation process.

### 7. Tests do not pass

Backend test collection failed with 7 import errors:

```text
ModuleNotFoundError: No module named 'middleware'
ModuleNotFoundError: No module named 'services'
ModuleNotFoundError: No module named 'main'
```

Affected tests:

```text
tests/test_csrf.py
tests/test_fallback.py
tests/test_generate.py
tests/test_integration_ac.py
tests/test_mimo_client.py
tests/test_quota.py
tests/test_session.py
```

This is separate from the SEO scope, but it means the current codebase is not in a clean verified state.

## What Is Implemented Already

The repository does have a useful SEO foundation:

- `dnd-prompt-forge/frontend/index.html`
- `dnd-prompt-forge/frontend/robots.txt`
- `dnd-prompt-forge/frontend/sitemap.xml`
- canonical tags on core static pages
- visible homepage FAQ
- homepage content sections and internal links

These are baseline SEO assets, not the autonomous static content system described by the scope document.

## Minimum Work Needed to Pass Phase 1

To satisfy the Phase 1 MVP described in the scope document, implementation should add:

1. A daily scheduler or GitHub Actions workflow.
2. A keyword candidate collector with Google Trends fallback support.
3. An LLM SEO decision contract implementation.
4. `dnd-prompt-forge/frontend/data/seo-pages.json`.
5. `dnd-prompt-forge/frontend/data/seo-failures.json`.
6. A static page generator that creates at least one real long-tail HTML page.
7. A registry-driven sitemap updater.
8. Visible FAQ/example/internal-link generation.
9. Canonical group handling.
10. `content_fingerprint` and similarity checks.
11. `docs/seo-runs/YYYYMMDD-*.md` run reports.
12. Generator prefill support in the frontend.
13. A deployment path that matches the scope: frontend static output outside Docker.

## Acceptance Result

Business acceptance should remain blocked.

The restored scope document is present, but the system it describes is not implemented in code or deployment configuration.
