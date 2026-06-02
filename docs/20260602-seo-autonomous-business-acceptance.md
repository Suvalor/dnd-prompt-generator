# SEO Autonomous Static Content System - Business Acceptance

Date: 2026-06-02
Scope requested: `docs/scope-change/20260602-seo-autonomous-static-content-system.md`
Acceptance type: business function acceptance

## Verdict

Not accepted.

The autonomous SEO static content system described by the requested scope is not implemented in the current workspace state.

The current repository has useful SEO basics such as a sitemap, robots.txt, canonical tags for core static pages, and long-tail URLs listed in the sitemap. However, it does not contain the autonomous daily SEO workflow, LLM decision pipeline, generated static pages, SEO registry, failure registry, Astro/SSG implementation, or scheduled automation required by the scope.

## Key Finding

The requested scope document itself is missing:

```text
docs/scope-change/20260602-seo-autonomous-static-content-system.md
```

The daily run simulation document is also missing:

```text
docs/scope-change/20260602-seo-autonomous-daily-run-simulation.md
```

Because the source scope is not present, this acceptance used the previously discussed requirements and the current repository state as the verification basis.

## Acceptance Matrix

| Business capability | Status | Evidence | Notes |
|---|---:|---|---|
| Frontend static SEO baseline | Partially passed | `frontend/index.html`, `frontend/robots.txt`, `frontend/sitemap.xml`, canonical tags exist. | Baseline exists, but long-tail pages are not real static pages. |
| Frontend not deployed to Docker | Failed | Root `docker-compose.yml` still builds `frontend` and exposes port `8081`. | Contradicts latest direction that frontend should not deploy to Docker. |
| Daily 00:00 scheduler | Failed | No `.github/` directory or workflow files found. | No cron job exists. |
| Google Trends / keyword data fetcher | Failed | No SEO worker/scripts found. | No module or API client for trends. |
| Search Console integration | Failed | No SEO worker/scripts found. | No Search Console API integration. |
| LLM keyword decision contract | Failed | No SEO worker/scripts found. | No classifier/scorer/structured JSON decision pipeline. |
| LLM-generated static content | Failed | No `frontend/generated/`, no generated SEO pages, no content registry. | Not implemented. |
| Astro SSG selection / migration path | Failed | No `astro.config.*`, no `src/content/seo-pages`, no package config. | Not implemented. |
| Long-tail page generator prefill | Failed | No prefill JSON/frontmatter/query handling found. | Existing `App` only has simple client-side route state for core generator type. |
| Sitemap automation | Failed | `sitemap.xml` exists manually, but no updater or registry exists. | Many sitemap URLs do not map to static files. |
| Canonical automation | Failed | Some static pages have canonical tags, but no canonical map/automation exists. | No generated-page canonical process found. |
| Internal link automation | Failed | Links exist in frontend sections/footer, but no optimizer/automation exists. | Manual/static only. |
| FAQ automation | Failed | Existing FAQ exists, but no generator/validator/JSON-LD matching automation exists. | Manual/static only. |
| Automated quality gates | Failed | No relevance, duplicate, helpful content, spam, HTML, build, cost, or content drift gates found. | Not implemented. |
| Content drift protection | Failed | No `content_fingerprint`, similarity checker, calibration docs, or health metrics found. | Not implemented. |
| Failure report follow-up | Failed | No `docs/seo-runs/`, no `seo-failures.json`. | Not implemented. |
| Static build/deploy pipeline | Failed | No frontend `package.json`, no `npm run build` path found in current project state. | Not implemented for SEO static output. |

## Verification Performed

Commands run:

```bash
find . -maxdepth 5 -type f
rg "seo|SEO|trend|sitemap|canonical|Astro|fingerprint|helpful|quota|MIMO|LLM|feedback|memory_rules|prefill"
docker compose config
pytest -q
node -e "<sitemap URL to local HTML existence check>"
test -f docs/scope-change/20260602-seo-autonomous-static-content-system.md
test -f docs/scope-change/20260602-seo-autonomous-daily-run-simulation.md
test -d .github
```

Results:

- `docker compose config`: passed.
- `pytest -q`: failed during collection with missing modules.
- Scope document: missing.
- Daily run simulation document: missing.
- `.github` workflows: missing.
- SEO generated page directory: missing.
- SEO registry/failure registry: missing.
- Astro config/content directory: missing.

## Sitemap-To-Static-Page Check

The sitemap lists long-tail URLs, but most do not have corresponding static HTML files.

Passed:

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

Business impact:

- Google may discover URLs in the sitemap that are served as the same SPA fallback page.
- These pages are not distinct static SEO content pages.
- This does not satisfy the autonomous static content system requirement.

## Backend/Test Health Note

Backend acceptance tests currently fail before execution:

```text
ModuleNotFoundError: No module named 'middleware'
ModuleNotFoundError: No module named 'services'
ModuleNotFoundError: No module named 'main'
```

This does not directly prove SEO failure, but it means the current test suite cannot be used as reliable acceptance evidence.

## Business Acceptance Conclusion

The implemented business function does not meet the requested autonomous SEO static content system.

Accepted baseline pieces:

- Existing static homepage.
- Existing sitemap and robots.txt.
- Existing long-tail SEO URL list in sitemap.
- Existing manual internal links and FAQ sections.

Not accepted:

- Daily autonomous SEO run.
- LLM keyword selection and scoring.
- LLM static content generation.
- New generated static pages.
- Sitemap/canonical/internal-link/FAQ/example automation.
- Astro/SSG content pipeline.
- Content drift and quality gates.
- Failure report loop.
- Static host deployment workflow.

## Required To Pass

Minimum pass criteria:

1. Restore or recreate the missing scope documents.
2. Add a scheduled SEO worker or GitHub Actions workflow.
3. Add keyword candidate input pipeline.
4. Add LLM decision JSON contract implementation.
5. Add `seo-pages.json` and `seo-failures.json`.
6. Generate at least one real static SEO page from the pipeline.
7. Update sitemap from the generated page registry.
8. Add canonical and visible FAQ/example content to generated page.
9. Add at least basic content quality gates.
10. Run a successful static build.
11. Produce a daily run report under `docs/seo-runs/`.

Suggested first acceptance target:

```text
One scheduled/manual SEO run creates:
- dnd-prompt-forge/frontend/generated/dragonborn-paladin-token-prompt.html
- dnd-prompt-forge/frontend/data/seo-pages.json
- dnd-prompt-forge/frontend/data/seo-failures.json
- docs/seo-runs/20260602-published.md
- updated dnd-prompt-forge/frontend/sitemap.xml
```
