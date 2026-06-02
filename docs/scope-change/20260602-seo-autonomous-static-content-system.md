# Autonomous SEO Static Content System

Date: 2026-06-02
Status: completed
Project: DND Prompt Forge

## Goal

Build an automated SEO growth system that increases Google exposure for DND Prompt Forge by discovering rising long-tail keywords and using an LLM to create or update useful static content.

New user requirements:

- Frontend is no longer deployed to Docker.
- The SEO automation should not use a human approval step.
- Every day, the system searches for long-tail keywords related to this project.
- Keywords with upward trend signals are included in the content update scope.
- LLM decides which keywords are worth acting on.
- LLM generates new static content and related SEO updates.

Important boundary:

- The system must not use hidden text, crawler-only content, cloaking, or keyword stuffing.
- All generated keyword coverage must appear as visible, useful content for users.

## Official SEO Constraints

Google Search Central guidance affects this design:

- Google spam policies prohibit hidden text/link abuse, keyword stuffing, and cloaking.
- Google helpful content guidance recommends people-first content, not content made primarily to manipulate rankings.
- Google supports sitemap submission through Search Console and Search Console API.
- Google Trends API is currently alpha/early-access, so a fallback keyword data provider may be needed.

Sources:

- https://developers.google.com/search/docs/essentials/spam-policies
- https://developers.google.com/search/docs/fundamentals/creating-helpful-content
- https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap
- https://developers.google.com/webmaster-tools/v1/sitemaps/submit
- https://developers.google.com/search/apis/trends

## Deployment Architecture

### Frontend

Frontend should be deployed as static files, not as a Docker runtime service.

Recommended targets:

- Cloudflare Pages
- Vercel static output
- Netlify
- GitHub Pages
- Static Nginx/CDN upload

Static output should include:

- `index.html`
- route HTML pages
- CSS/JS assets
- `robots.txt`
- `sitemap.xml`
- `ads.txt`
- generated SEO pages

### SSG Selection

Decision:

- Use Astro for the SEO static site layer.

Rationale:

- The project needs many static, crawlable content pages.
- Most generated pages are content-heavy and need minimal client JavaScript.
- Astro supports static output, reusable layouts, content collections, and route generation.
- The existing generator UI can be embedded as a client-side island while SEO pages remain static HTML.

Rejected options:

- Next.js: powerful but heavier than needed for a mostly static SEO site.
- Raw HTML generation only: easy at first, but harder to maintain canonical groups, reusable templates, and content collections at scale.

Target structure after migration:

```text
dnd-prompt-forge/
├── astro.config.mjs
├── src/
│   ├── layouts/
│   ├── pages/
│   ├── components/
│   └── content/
│       └── seo-pages/
├── frontend/                  # existing static assets during migration
└── dist/                      # static output
```

Migration rule:

- Phase 1 may keep the current static HTML build script.
- Phase 2 should move generated SEO pages into Astro content collections.
- Do not design the automation around Next.js unless this decision is reopened.

Astro migration trigger:

- Start Astro migration when any one condition is met:
  - generated SEO pages reach 50 published pages;
  - the autonomous SEO system has run for 14 consecutive days;
  - the current static HTML generator needs a second reusable page template;
  - more than 20% of daily generated changes touch shared layout/header/footer markup.
- Until a trigger is met, keep the current static HTML build as the MVP path.
- Once a trigger is met, freeze new template expansion until Astro migration is complete.

### Backend / Worker

The SEO automation is not part of the frontend runtime.

Use a scheduled worker:

- GitHub Actions cron
- VPS cron
- Cloudflare Worker scheduled trigger
- Small server worker

Recommended first implementation:

- GitHub Actions scheduled workflow.
- It runs once per day.
- It generates or updates static content files.
- It commits changes to the repository or writes them to a deployment branch.
- Static hosting then redeploys the frontend.

## Data Model Integration

The SEO automation is static-content-first. It should not store generated SEO pages in the runtime SQLite database by default.

Reason:

- SEO pages must be deployable as static files.
- Search crawlers need stable, crawlable HTML.
- The current SQLite database is runtime/backend state and should not be required for static page rendering.

### Static SEO Registry

Use a repository-tracked registry for generated content:

```text
dnd-prompt-forge/frontend/data/seo-pages.json
```

Or, after Astro migration:

```text
dnd-prompt-forge/src/content/seo-pages/*.md
```

Registry fields:

```json
{
  "slug": "dragonborn-paladin-token-prompt",
  "canonical_url": "https://dndpromptforge.com/dragonborn-paladin-token-prompt",
  "primary_keyword": "dragonborn paladin token prompt",
  "canonical_group": "dragonborn-paladin-token",
  "intent": "race_class_page",
  "status": "published",
  "created_at": "2026-06-03",
  "updated_at": "2026-06-03",
  "last_trend_score": 72,
  "last_helpful_content_score": 86,
  "source_keywords": [
    "dragonborn paladin token prompt",
    "dnd dragonborn paladin vtt token prompt"
  ],
  "related_pages": [
    "/dnd-token-prompt-generator",
    "/midjourney-dnd-character-prompts"
  ],
  "content_fingerprint": "sha256:..."
}
```

### Runtime Backend Feedback

Runtime feedback can inform SEO, but should not directly publish content.

Possible feedback sources:

- `feedback_events`: reasons like "too generic", "missing token guidance", or "wrong style".
- `prompt_requests`: popular output types, races, classes, target models.
- `memory_rules`: recurring prompt improvement rules.

Recommended bridge:

```text
backend SQLite -> weekly anonymized SEO signal export -> SEO worker input
```

Exported signal example:

```json
{
  "top_prompt_types": ["token", "npc", "portrait"],
  "top_race_class_pairs": [
    ["dragonborn", "paladin"],
    ["tiefling", "warlock"]
  ],
  "feedback_themes": [
    "token prompts need clearer top-down framing",
    "npc prompts need stronger role-defining traits"
  ],
  "memory_rule_summaries": [
    "avoid generic fantasy wording",
    "include VTT crop guidance for token prompts"
  ]
}
```

Privacy rules:

- Do not export raw user text by default.
- Do not export IP, cookie, fingerprint, or request IDs.
- Summarize feedback themes before feeding them into SEO generation.

How `memory_rules` can be reused:

- Use active memory rules as content-quality guidance for examples.
- Do not treat `memory_rules` as SEO keywords.
- Do not publish user feedback verbatim.

## High-Level Daily Flow

```text
Daily 00:00
  -> Fetch keyword trend data
  -> Filter DND / fantasy / prompt-generator relevance
  -> LLM clusters keywords by intent
  -> LLM scores trend + relevance + content value
  -> LLM chooses actions
  -> LLM generates static content updates
  -> Automated quality gates run
  -> Update sitemap, canonical, internal links, FAQ, examples
  -> Build static site
  -> Deploy static frontend
  -> Submit/refresh sitemap signal
  -> Log result and metrics
```

No human approval step is required, but the system must still have automated gates.

## Data Sources

### Primary

Google Trends API, if access is approved.

Use cases:

- Rising queries.
- Related queries.
- Category/time-window trend signals.

### Fallback

If Google Trends API access is unavailable:

- Third-party keyword API.
- SERP API.
- Manual seed list expanded by LLM.
- Google Search Console query data after the site has impressions.

### Search Console

Once the site is live:

- Pull queries with impressions but low CTR.
- Pull pages with declining impressions.
- Pull pages with high impressions and weak average position.
- Use this data as the strongest optimization input.

### Runtime Product Signals

Optional weekly source:

- Anonymized backend usage summary.
- Feedback themes.
- Generator mode popularity.
- Copy button click counts if analytics are available.

Use this to prioritize pages that match real product usage, not only trend data.

## Keyword Pipeline

### 1. Seed Terms

Initial seed set:

```text
dnd character prompt generator
dnd ai image prompt
dnd token prompt generator
dnd npc prompt generator
dnd monster prompt generator
fantasy character prompt
midjourney dnd character prompt
stable diffusion dnd prompt
chatgpt dnd image prompt
vtt token prompt
```

### 2. Candidate Collection

For each seed term, fetch:

- Rising queries.
- Related queries.
- Long-tail variants.
- Question-style variants.
- Model-specific variants.
- Race/class variants.
- Token/NPC/monster/scene variants.

### 3. Normalization

Normalize:

- Lowercase.
- Trim whitespace.
- Deduplicate near matches.
- Remove unrelated D&D meaning collisions.
- Remove copyrighted character-targeting queries unless used only as negative safety examples.

### 4. LLM Intent Classification

Classify each keyword into one of:

- `tool_page`
- `race_class_page`
- `model_guide`
- `how_to_guide`
- `example_gallery`
- `faq_update`
- `internal_link_update`
- `reject`

### 5. LLM Scoring

Score each candidate:

```text
trend_score: 0-100
project_relevance: 0-100
user_value: 0-100
content_uniqueness: 0-100
commercial_policy_risk: 0-100
spam_risk: 0-100
```

Recommended action threshold:

- Act when:
  - `trend_score >= 55`
  - `project_relevance >= 75`
  - `user_value >= 70`
  - `content_uniqueness >= 60`
  - `spam_risk <= 35`

Reject when:

- Keyword is unrelated.
- Page would be thin or duplicative.
- Keyword requires hidden/crawler-only text to be useful.
- Query mainly targets copyrighted official art or impersonation.
- Trend is too weak or too short-lived.

## LLM Decision Contract

The LLM must output structured JSON:

```json
{
  "date": "2026-06-02",
  "selected_keywords": [
    {
      "keyword": "dragonborn paladin token prompt",
      "intent": "race_class_page",
      "action": "create_page",
      "target_url": "/dragonborn-paladin-token-prompt",
      "reason": "Rising token-specific long-tail query with clear user intent.",
      "scores": {
        "trend_score": 72,
        "project_relevance": 94,
        "user_value": 88,
        "content_uniqueness": 76,
        "spam_risk": 18
      }
    }
  ],
  "rejected_keywords": [
    {
      "keyword": "official vecna art generator",
      "reason": "Copyright and official-character risk."
    }
  ]
}
```

Additional required fields:

```json
{
  "estimated_llm_cost_usd": 0.42,
  "token_budget": {
    "decision_tokens": 6000,
    "generation_tokens": 18000,
    "validation_tokens": 4000
  },
  "ssg_target": "astro",
  "data_model_action": "create_static_registry_entry",
  "prefill": {
    "generator_type": "token",
    "race": "Dragonborn",
    "class_role": "Paladin",
    "style": "painterly",
    "mood": "heroic",
    "target_model": "midjourney"
  }
}
```

The worker must reject LLM output if required fields are missing.

## LLM Cost And Rate Limiting

Daily automation must have a strict budget.

Environment variables:

```text
SEO_LLM_DAILY_TOKEN_BUDGET=100000
SEO_LLM_DAILY_COST_BUDGET_USD=5.00
SEO_LLM_MAX_CANDIDATES_PER_RUN=100
SEO_LLM_MAX_GENERATED_PAGES_PER_RUN=3
SEO_LLM_MAX_UPDATED_PAGES_PER_RUN=10
SEO_LLM_MAX_RETRIES_PER_STEP=1
```

Budget policy:

- Stop before content generation if candidate analysis already exceeds 50% of daily token budget.
- Stop creating new pages when cost budget is exceeded.
- Prefer updating existing pages over creating new pages when budget is tight.
- Cache keyword classification results for 7 days.
- Cache canonical group assignments permanently unless the page registry changes.

LLM call classes:

```text
classification: low-cost model allowed
scoring: low/medium-cost model allowed
page generation: high-quality model required
validation: low/medium-cost model allowed
repair: high-quality model only for publishable candidates
```

Rate limiting:

- Limit LLM calls per daily run.
- Limit external keyword API calls per daily run.
- Add exponential backoff for provider 429/5xx errors.
- If a provider limit is hit, write a partial run report and stop publishing new content.

## Content Actions

### `create_page`

Create a new static HTML route.

Use when:

- Keyword has distinct intent.
- Existing pages cannot satisfy the query.
- Page can include useful examples and generator entry point.

Generated files:

```text
dnd-prompt-forge/frontend/generated/<slug>.html
```

Page requirements:

- Unique title.
- Unique meta description.
- Canonical URL.
- Visible H1.
- Visible helpful intro.
- Generator entry point or prefilled example.
- 3-8 copyable examples.
- FAQ section.
- Related internal links.
- No hidden keyword block.

### Long-Tail Page Generator Prefill

Every long-tail page should connect to the core generator through prefilled state.

Supported options:

1. Query string prefill:

```text
/?type=token&race=Dragonborn&class=Paladin&style=painterly&mood=heroic&model=midjourney
```

2. Route-level embedded JSON:

```html
<script type="application/json" id="generator-prefill">
{
  "type": "token",
  "race": "Dragonborn",
  "klass": "Paladin",
  "style": "painterly",
  "mood": "heroic",
  "model": "midjourney"
}
</script>
```

3. Astro content frontmatter:

```yaml
prefill:
  type: token
  race: Dragonborn
  klass: Paladin
  style: painterly
  mood: heroic
  model: midjourney
```

Recommended decision:

- Use Astro frontmatter after SSG migration.
- Use embedded JSON during current static HTML phase.

Frontend generator requirement:

- On page load, check for `#generator-prefill`.
- If present, prefill the generator state.
- Show a visible CTA: "Open this Dragonborn Paladin token prompt in the generator."
- Do not hide generated keyword content in the prefill JSON; it is functional state only.

### `update_page`

Update an existing static page.

Use when:

- Existing page already matches the intent.
- New keyword is a variation or subtopic.

Possible updates:

- Add visible FAQ.
- Add example prompt.
- Add a related link.
- Improve title/meta.
- Update content section.
- Update `lastmod` in sitemap.

### `update_faq`

Add visible FAQ items to the most relevant page.

Rules:

- FAQ answer must be useful by itself.
- FAQ question should match real query language.
- JSON-LD FAQ can be added only if the FAQ is visible on page.

### `update_examples`

Add examples derived from keyword intent.

Example types:

- Positive prompt.
- Negative prompt.
- Short prompt.
- Model-specific note.
- Token export note.

### `update_internal_links`

Add natural links between related pages.

Rules:

- Anchor text must read naturally.
- Avoid exact-match anchor spam.
- Link only when the target helps the user continue the task.

### `reject`

Do nothing.

Use when:

- Low value.
- Spam risk.
- Duplicate intent.
- Policy risk.
- No clear page value.

## Page Template

Every generated page should use this structure:

```text
title
meta description
canonical
H1
short intro
generator module or CTA
examples
how to use this prompt
negative prompt guidance
related prompt types
FAQ
internal links
```

Example title:

```text
Dragonborn Paladin Token Prompt Generator | DND Prompt Forge
```

Example meta:

```text
Create a top-down Dragonborn Paladin VTT token prompt with positive and negative prompt examples for Midjourney, ChatGPT, and Stable Diffusion.
```

## Sitemap Automation

For each generated or updated page:

1. Add or update URL in `frontend/sitemap.xml`.
2. Set `lastmod` to the generation date.
3. Use `priority` based on page type:
   - homepage: `1.0`
   - core tool page: `0.9`
   - model guide: `0.8`
   - race/class long-tail: `0.7`
   - FAQ/example page: `0.6`
4. Use `changefreq`:
   - core pages: `weekly`
   - long-tail pages: `monthly`
   - trend pages: `weekly` while active, then `monthly`.

Example:

```xml
<url>
  <loc>https://dndpromptforge.com/dragonborn-paladin-token-prompt</loc>
  <lastmod>2026-06-02</lastmod>
  <changefreq>monthly</changefreq>
  <priority>0.7</priority>
</url>
```

## Canonical Automation

The LLM must assign every candidate to a canonical group.

Canonical rules:

- If intent is unique, create a new canonical page.
- If intent overlaps an existing page, update the existing page instead.
- Do not create multiple pages for synonyms.

Examples:

```text
dnd token prompt generator
vtt token prompt generator
dnd ai token prompt
```

Canonical target:

```text
/dnd-token-prompt-generator
```

Generated page must include:

```html
<link rel="canonical" href="https://dndpromptforge.com/dnd-token-prompt-generator" />
```

## Internal Link Automation

For every created or updated page:

1. Identify 3-6 related pages.
2. Add visible links in a related section.
3. Update source pages that should link to the new page.
4. Avoid sitewide link spam.

Good related link examples:

```text
Create more VTT-ready prompts with the DND token prompt generator.
Adapt this character for Midjourney with the Midjourney DND prompt guide.
Build an NPC version with the DND NPC prompt generator.
```

## FAQ Automation

LLM generates 2-5 FAQs per page.

FAQ quality rules:

- Must answer a real user question.
- Must be visible on the page.
- Must not duplicate existing FAQ.
- Must avoid unsupported claims.
- Must include practical prompt guidance.

Example:

```text
Q: How do I make a Dragonborn Paladin token prompt?
A: Use a top-down view, centered single figure, clean readable silhouette, 1:1 framing, radiant armor details, and a simple background that will crop well in a virtual tabletop.
```

## Example Content Automation

LLM generates examples based on page intent.

Example block:

```text
Positive prompt:
top-down view, centered single figure, a bronze dragonborn paladin, gilded plate armor, shield raised, radiant oath magic effects, clean readable silhouette, simple parchment background, circular VTT token framing, painterly fantasy illustration, intricate detail

Negative prompt:
background clutter, multiple figures, off-center, busy scenery, extra limbs, bad anatomy, watermark, text, logo, cropped
```

Rules:

- Examples must be copyable.
- Examples must match the page keyword intent.
- Negative prompt must be useful, not generic filler only.
- Avoid official copyrighted character names unless the user explicitly supplies them.

## Automated Quality Gates

Although there is no human approval step, the system must have automated gates before publishing.

### Gate 1: Relevance

Reject if:

- Keyword is not about DND, fantasy art prompts, tabletop tokens, NPCs, monsters, scenes, or compatible AI image prompt use.

### Gate 2: Duplicate Intent

Reject or update existing page if:

- New page overlaps an existing canonical group.

### Gate 3: Helpful Content

Reject if:

- Page has no useful examples.
- Page is only keyword variation text.
- Page would not help a real user generate a better prompt.

### Gate 4: Spam Risk

Reject if:

- Keyword appears unnaturally often.
- Content contains hidden text.
- Content is crawler-only.
- Page is a near-duplicate.
- Generated content is mostly boilerplate.

### Gate 5: HTML Validity

Reject if:

- Required tags are missing.
- Canonical is invalid.
- Sitemap URL is invalid.
- FAQ JSON-LD does not match visible FAQ.

### Gate 6: Build

Reject if:

- Static build fails.
- Generated route missing.
- Sitemap cannot be parsed.

### Gate 7: Cost And Rate Limit

Reject or defer if:

- Daily LLM token budget is exceeded.
- Daily LLM cost budget is exceeded.
- External API rate limit is exceeded.
- Required cached data is unavailable and would force too many LLM calls.

### Gate 8: Content Drift

Reject or defer if:

- New page is too similar to an existing page.
- Generated examples differ only by race/class names.
- The page repeats the same boilerplate sections without new guidance.
- Helpful-content score drops below threshold.

Similarity thresholds:

```text
title_similarity < 0.85
meta_similarity < 0.85
body_similarity < 0.82
example_similarity < 0.78
faq_similarity < 0.80
```

Recommended implementation:

- Use embeddings or TF-IDF cosine similarity.
- Compare against canonical group pages and recent generated pages.
- Keep an n-gram overlap check for cheap duplicate detection.
- Track `content_fingerprint` in the SEO registry.

`content_fingerprint` definition:

- Compute from normalized visible page text content.
- Exclude dynamic timestamps, build hashes, deployment IDs, analytics snippets, JSON-LD formatting differences, and canonical URL protocol/domain changes.
- Include visible headings, paragraph text, FAQ text, example prompts, and related-link anchor text.
- Normalize by lowercasing, collapsing whitespace, removing HTML tags, decoding entities, and sorting repeated boilerplate blocks out of the hash input.
- Hash with SHA-256 and store as `sha256:<hex>`.

Similarity threshold calibration:

- Build an initial seed page set from homepage, prompt type pages, model guide pages, and 5-10 race/class pages.
- Run pairwise similarity across the seed set.
- Confirm that clearly distinct pages pass the thresholds and near-duplicate template variants fail.
- Recalibrate thresholds after the first 25 generated pages and again after the first 100 generated pages.
- Store calibration snapshots in `docs/seo-runs/similarity-calibration-YYYYMMDD.md`.

## Publishing Model Without Human Review

Recommended safe automation:

```text
LLM decides -> static content generated -> automated gates -> commit -> deploy
```

If a gate fails:

```text
write failure report -> do not publish that page
```

Failure report path:

```text
docs/seo-runs/YYYYMMDD-failed-candidates.md
```

Successful run report path:

```text
docs/seo-runs/YYYYMMDD-published.md
```

## Failure Report Follow-Up

Failure reports are not dead-end logs. They feed the next run.

Each failed candidate should include:

```json
{
  "keyword": "dragonborn paladin token prompt",
  "failed_gate": "content_drift",
  "reason": "Too similar to /dnd-token-prompt-generator",
  "recommended_next_action": "update_existing_page",
  "retry_after_days": 14,
  "retry_count": 1
}
```

Next-run handling:

- `retry_after_days` blocks immediate repeated attempts.
- `retry_count >= 2` sends candidate to `defer_long_term`.
- If `recommended_next_action` is present, feed it to LLM as a constraint.
- If repeated failures are caused by content drift, update existing canonical page instead of creating a new page.

Failure state file:

```text
dnd-prompt-forge/frontend/data/seo-failures.json
```

States:

```text
retry_later
defer_long_term
update_existing_only
blocked_policy
blocked_duplicate
```

## Repository Outputs

Daily job may modify:

```text
dnd-prompt-forge/frontend/generated/*.html
dnd-prompt-forge/frontend/sitemap.xml
dnd-prompt-forge/frontend/robots.txt
dnd-prompt-forge/frontend/index.html
dnd-prompt-forge/frontend/pages/*.html
dnd-prompt-forge/frontend/data/seo-pages.json
dnd-prompt-forge/frontend/data/seo-failures.json
docs/seo-runs/*.md
```

Daily job must not modify:

```text
backend provider secrets
.env
runtime database files
node_modules
dist
```

## Scheduling

Default:

```text
0 0 * * *
```

Use project timezone:

```text
Asia/Shanghai
```

Recommended GitHub Actions steps:

1. Checkout repository.
2. Install dependencies.
3. Fetch trend/search data.
4. Run LLM keyword decision.
5. Generate content.
6. Run automated gates.
7. Run static build.
8. Commit generated changes.
9. Trigger static hosting redeploy.
10. Submit sitemap or ping Search Console workflow.

With SSG selected:

```text
1. Checkout repository.
2. Install Node dependencies.
3. Fetch trend/search/product signals.
4. Run LLM keyword decision with budget limits.
5. Generate Astro content files or static HTML fallback.
6. Update SEO registry and failure registry.
7. Run content drift and quality gates.
8. Run `npm run build`.
9. Commit generated source content, not `dist`.
10. Static host builds and deploys.
```

## Search Console Integration

After deployment:

1. Submit `sitemap.xml` in Search Console.
2. Optionally use Search Console API to submit sitemap URL after updates.
3. Pull query/page data weekly.
4. Feed underperforming pages into the next LLM optimization cycle.

Metrics:

- Impressions.
- Clicks.
- CTR.
- Average position.
- Indexed page count.
- Pages discovered but not indexed.

## Rollback Plan

Because no human approval is used, rollback must be easy.

Required:

- Each daily run commits separately.
- Commit message includes run date and number of pages changed.
- Store generated run report.
- If Search Console or analytics show a bad trend, revert the daily commit.
- Add a maximum daily page creation limit.

Recommended page creation limits:

- First month: max 1-3 new pages/day.
- After stable indexing: max 5 new pages/day.
- Updates to existing pages can be higher, but still capped.

## MVP Version

Phase 1 MVP:

- Frontend static deployment only.
- Daily keyword collection.
- LLM selection and scoring.
- Generate run report.
- Create or update at most 1 static page/day.
- Update sitemap.
- Run automated gates.
- Commit generated page.
- Use current static HTML build script if Astro migration is not ready.
- Track SEO pages in `seo-pages.json`.
- Track failed candidates in `seo-failures.json`.
- Enforce daily LLM token and cost budgets.

Phase 2:

- Migrate SEO static pages to Astro.
- Add Search Console query data.
- Add canonical group memory.
- Add internal link graph optimizer.
- Add FAQ JSON-LD validation.
- Add generator prefill from Astro frontmatter.
- Add backend feedback export as SEO signal input.

Phase 3:

- Add larger programmatic SEO templates.
- Add automatic pruning/noindex recommendations.
- Add ranking feedback loop.
- Add content drift dashboards and page refresh scheduling.
- Add internal content-quality health monitoring:
  - average `helpful_content_score` over time;
  - median `content_uniqueness` by page type;
  - percentage of pages below quality threshold;
  - duplicate/canonical collision rate;
  - failed-candidate retry rate;
  - pages with impressions but low CTR;
  - pages crawled but not indexed;
  - pages with declining average position over 28 days.

## Final Recommendation

Use LLM autonomy, but constrain it with strict structured outputs and automated quality gates.

The system should not hide keywords or create pages just because a keyword is trending. It should only publish visible static content when the LLM can produce a useful page with examples, FAQ, canonical handling, internal links, and sitemap updates.

This keeps the workflow fully automated while reducing the risk of spam-like SEO behavior.

## AutoDev 执行进度

- [x] Phase 1：需求对齐 / PRD
- [x] Phase 1.5：价值审查（SIMPLER_PROPOSAL → 用户坚持原方案）
- [x] Phase 2：设计与架构
- [x] Phase 3：实现（4个Sprint）
- [x] Phase 4：代码审查（3轮，全部修复通过）
- [x] Phase 5：业务验收（14个AC全部PASS）
- [x] Phase 6：部署验证

### 最新状态
- 当前阶段：全部完成
- 最近更新时间：2026-06-02
- 变更文件：backend/seo_worker/*.py (9个模块), frontend/js/app.jsx, frontend/js/generator.jsx, docker-compose.yml, .github/workflows/seo-daily.yml, frontend/Dockerfile.deprecated
- 验证命令：pytest dnd-prompt-forge/backend/tests/ -q
- 验证结果：196 passed, 1 pre-existing minor failure
- 阻塞项：无
- 假设与取舍：(1) Google Trends API 为 alpha 产品，Phase 1 以 LLM 扩展种子词作为 fallback；(2) Phase 1 不做 Astro 迁移，使用 Jinja2 HTML 模板；(3) SEO Worker 作为 Python CLI 模块而非独立服务；(4) 前端部署为纯静态文件（不进 Docker）
