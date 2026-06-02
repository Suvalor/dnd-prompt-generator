# Architecture Specification: SEO Autonomous Static Content System (Phase 1 MVP)

> Version: 1.0 | Date: 2026-06-02 | Author: architect | Status: DRAFT
> Project: DND Prompt Forge | Experiment ID: 003

---

## 1. Executive Summary

Core Flow: Keyword Discovery → Classification & Scoring → Page Generation (LLM + Jinja2) → Quality Gate → Publish as Static HTML.

Key Constraints:
- SEO Worker is an independent Python module within the backend codebase, NOT a separate service
- Existing backend API endpoints MUST NOT be modified
- Phase 1 does NOT include Astro migration
- Backend source code loss is a blocking pre-requisite that MUST be resolved first

---

## 2. Baseline Reconnaissance

### Current Architecture

| Aspect | Current State |
|--------|--------------|
| Backend Framework | Python FastAPI (single file: main.py ~270 lines) |
| Backend Source Status | PARTIAL LOSS — mimo_client.py, fallback.py, data models exist only as .pyc |
| Frontend | Standalone HTML + Babel JSX |
| Database | SQLite (feedback memory system) |
| LLM Integration | DeepSeek API (primary) + MiMo (fallback) |
| Containerization | Docker Compose: backend + frontend (Nginx) |
| Dependencies | fastapi, uvicorn, httpx, pydantic, python-dotenv, deepseek-sdk |

---

## 3. Architecture Decision Records (ADRs)

### ADR-1: SEO Worker as Independent Python Module vs Separate Service
- **Decision**: Independent Python module within backend codebase (`backend/seo_worker/`)
- **Rationale**: Shares LLM client code, shares .env config, runs as CLI entry point. Zero additional container overhead.

### ADR-2: Jinja2 vs String Template for HTML Generation
- **Decision**: Jinja2
- **Rationale**: Auto-escaping prevents XSS from LLM output. Template inheritance for shared layout. Industry standard.

### ADR-3: GitHub Actions vs VPS Cron for Scheduling
- **Decision**: VPS cron for Phase 1
- **Rationale**: Simple crontab entry. Direct filesystem access. No external dependencies. Phase 2 can add GitHub Actions.

### ADR-4: TF-IDF vs Embeddings for Content Drift Detection
- **Decision**: TF-IDF + cosine similarity for Phase 1
- **Rationale**: No heavy dependencies (no torch). Millisecond computation. Sufficient for drift detection.

### ADR-5: Backend Source Code Recovery Strategy
- **Decision**: Rewrite from test specifications + main.py imports
- **Rationale**: Tests define exact behavioral contract. Rewriting against tests guarantees behavioral equivalence. Clean, readable, maintainable code.

---

## 4. System Boundary & Module Topology

### Module Physical Layout

```
dnd-prompt-forge/backend/
├── main.py                          # EXISTING — FastAPI app (DO NOT MODIFY endpoints)
├── requirements.txt                 # EXISTING — Add: jinja2, scikit-learn
├── mimo_client.py                   # REWRITE — MiMo LLM client
├── fallback.py                      # REWRITE — Fallback LLM orchestrator
├── models.py                        # REWRITE — Pydantic data models
├── quota.py                         # REWRITE — Session quota tracker
├── seo_worker/                      # NEW — SEO Worker module
│   ├── __init__.py
│   ├── __main__.py                  # CLI entry: python -m seo_worker run
│   ├── config.py                    # Worker configuration
│   ├── discoverer.py                # Keyword discovery
│   ├── classifier.py                # Classification + scoring
│   ├── generator.py                 # HTML page generation (Jinja2 + LLM)
│   ├── quality_gate.py              # Quality validation
│   ├── publisher.py                 # Static file output + sitemap update
│   ├── registry.py                  # Page/failure registry (JSON)
│   ├── drift_detector.py            # Content drift detection (TF-IDF)
│   └── templates/                   # Jinja2 HTML templates
│       ├── base.html
│       ├── character_page.html
│       ├── token_page.html
│       ├── monster_page.html
│       └── scene_page.html
├── seo_data/                        # Worker runtime data
│   ├── seo-pages.json
│   ├── seo-failures.json
│   └── seo-run-reports/
└── tests/
    ├── test_seo_worker/             # NEW — SEO Worker tests
    └── conftest.py
```

### Generated Output Location

```
dnd-prompt-forge/frontend/
├── generated/                       # SEO-generated static pages
│   ├── tiefling-warlock-prompt-generator/
│   │   └── index.html
│   └── ...
└── sitemap.xml                      # Auto-updated by publisher
```

---

## 5. Strict Contracts

### 5.1 Discoverer

```python
class KeywordCandidate:
    keyword: str
    source: Literal["seed_list", "trend_api", "manual"]
    volume: int | None
    competition: float | None
    discovered_at: str

class Discoverer:
    def __init__(self, config: WorkerConfig): ...
    async def discover(self) -> list[KeywordCandidate]: ...
```

### 5.2 Classifier

```python
class ClassifiedKeyword(KeywordCandidate):
    page_type: Literal["character", "token", "monster", "scene"]
    race: str | None
    character_class: str | None
    theme: str | None
    relevance_score: float

class Classifier:
    def __init__(self, config: WorkerConfig): ...
    async def classify(self, candidates: list[KeywordCandidate]) -> list[ClassifiedKeyword]: ...
```

### 5.3 Generator

```python
class GeneratedPage:
    slug: str
    page_type: str
    title: str
    meta_description: str
    html_content: str
    llm_raw_output: dict
    generated_at: str

class Generator:
    def __init__(self, config: WorkerConfig, llm_client: FallbackLLM): ...
    async def generate(self, keyword: ClassifiedKeyword) -> GeneratedPage: ...
```

### 5.4 Quality Gate

```python
class GateResult:
    passed: bool
    score: float
    checks: dict[str, CheckDetail]
    failure_reasons: list[str]

class QualityGate:
    def __init__(self, config: WorkerConfig): ...
    async def evaluate(self, page: GeneratedPage) -> GateResult: ...
```

Checks: min_word_count (>=800), has_h1, has_meta_description, no_placeholder_text, has_json_ld, keyword_in_title, keyword_in_meta, no_profanity, dnd_relevance

### 5.5 Publisher

```python
class PublishResult:
    slug: str
    url_path: str
    file_path: str
    published_at: str

class Publisher:
    def __init__(self, config: WorkerConfig): ...
    async def publish(self, page: GeneratedPage) -> PublishResult: ...
    async def rollback(self, slug: str) -> None: ...
```

### 5.6 Registry

```python
class PageRecord:
    slug: str
    keyword: str
    page_type: str
    status: Literal["published", "pending", "stale"]
    url_path: str
    published_at: str | None
    last_checked_at: str | None
    drift_score: float | None
    generation_count: int

class FailureRecord:
    keyword: str
    page_type: str | None
    status: Literal["retry_later", "defer_long_term", "update_existing_only", "blocked"]
    failure_reasons: list[str]
    attempt_count: int
    last_attempt_at: str
    next_retry_after: str | None

class Registry:
    def __init__(self, data_dir: Path): ...
    def get_published_slugs(self) -> set[str]: ...
    def get_failed_keywords(self) -> set[str]: ...
    def add_page(self, record: PageRecord) -> None: ...
    def add_failure(self, record: FailureRecord) -> None: ...
    def get_retryable_failures(self) -> list[FailureRecord]: ...
    def get_stale_pages(self, threshold_days: int) -> list[PageRecord]: ...
```

### 5.7 Drift Detector

```python
class DriftResult:
    slug: str
    similarity: float
    is_drifted: bool
    checked_at: str

class DriftDetector:
    def __init__(self, config: WorkerConfig): ...
    async def check(self, existing_html: str, fresh_html: str) -> DriftResult: ...
```

---

## 6. State Machine Design

### Keyword Candidate States

discovered → classified → scored → selected → generated → gated → passed → published
                                                                      → failed → retry_later → defer_long_term → blocked/update_existing_only

### Failure States

retry_later: next_retry_after = last_attempt_at + 24h, attempt_count < 3
defer_long_term: attempt_count >= 3, requires manual review
blocked: permanently rejected
update_existing_only: can only update existing pages, not create new ones

---

## 7. Security & Performance Red Lines

- **Single-instance guarantee**: File lock (`seo_data/.worker.lock`)
- **Idempotent page generation**: Overwrite existing slug
- **Atomic file writes**: write-to-tmp-then-rename pattern
- **Max pages per run**: 5 (configurable)
- **LLM cost control**: Daily budget $0.50, 2s delay between calls
- **XSS prevention**: Jinja2 autoescape=True, no `| safe` for LLM content
- **Path traversal prevention**: Slug sanitized to `[a-z0-9-]` only
- **Backup before overwrite**: Previous version saved to `seo_data/backups/`

---

## 8. Sprint Planning

### Sprint 1: Pre-requisite Fixes + Architecture Setup (2 days)
- Rewrite mimo_client.py, fallback.py, models.py, quota.py from test specs
- Create seo_worker/ package skeleton
- Add jinja2, scikit-learn to requirements.txt
- Create seo_data/ directory with initial JSON files

### Sprint 2: Core Pipeline (3 days)
- Implement discoverer, classifier, generator, quality_gate, publisher, registry
- Create Jinja2 templates
- Write tests
- Implement CLI orchestration

### Sprint 3: Integration + Frontend + Deployment (2 days)
- Update docker-compose.yml for generated/ volume mount
- Add Nginx location rule for /generated/ paths
- Implement drift_detector
- End-to-end integration test
- Set up VPS cron job

### Sprint 4: Testing + Acceptance (1 day)
- Run Worker for 5 consecutive days
- Manual SEO audit of generated pages
- Performance and resilience testing
- LLM cost tracking verification

---

## 9. Developer Pre-flight Checklist

### [BLOCKING] Items
- Run `pytest tests/` and confirm ALL existing tests pass before touching code
- Jinja2 Environment MUST be created with `autoescape=True`
- Slug generation MUST sanitize to `[a-z0-9-]` only
- All JSON file writes MUST use write-tmp-then-rename pattern
- Worker file lock MUST be checked at startup

### Known Pitfalls
1. DeepSeek may return JSON wrapped in markdown code fences — strip before parsing
2. sitemap.xml is XML — parse properly, don't regex
3. Jinja2 template inheritance requires `{% extends "base.html" %}`
4. TF-IDF on HTML must strip tags first
5. Nginx may serve stale content — consider `sendfile off;` for /generated/