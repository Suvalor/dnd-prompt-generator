# 项目需求文档（PRD）— SEO Autonomous Static Content System Phase 1 MVP

## 项目概述

为 DND Prompt Forge 构建自动化 SEO 静态内容系统 Phase 1 MVP。系统每日自动发现长尾关键词，LLM 决策筛选后生成/更新静态 SEO 页面，自动化处理 sitemap/canonical/internal-link/FAQ，通过质量门禁后 commit 并部署，全程无需人工审批。

当前代码库状态：21/22 项需求 FAILED，仅"现有 SEO 基线"部分通过。后端源码丢失（仅 .pyc），前端仍部署在 Docker，无 Astro/SSG 层，无自动化流水线，sitemap 中 16 个长尾 URL 无对应 HTML 文件。

## 目标用户与使用场景

1. **系统运维者/站长**: 运行和监控每日 SEO 自动化流水线，通过 docs/seo-runs/ 报告了解每日产出和质量指标。
2. **终端用户（DND 玩家/DM/VTT 用户）**: 通过 Google 搜索"DND dragonborn paladin token prompt"等长尾关键词到达高质量静态内容页，页面引导用户使用核心 prompt generator 工具。

## 核心功能列表（P0/P1/P2 优先级）

### P0 — Phase 1 MVP 必须交付

| 编号 | 功能 | 描述 |
|------|------|------|
| P0-1 | 后端源码恢复 | 从 .pyc 提取/重写 backend/main.py、models/、middleware/、services/、routers/，使 pytest 可运行 |
| P0-2 | 前端从 Docker 剥离 | 修改 docker-compose.yml 移除 frontend 服务，前端改为纯静态文件部署 |
| P0-3 | SEO Worker 核心 | Python 模块：关键词发现 → LLM 决策 → 内容生成 → 质量门禁 → 注册表更新 → 报告输出 |
| P0-4 | 关键词发现 | 种子词扩展 + Google Trends API（如有访问权）+ LLM 扩展 fallback |
| P0-5 | LLM 决策合约 | 结构化 JSON 输出：选词/打分/动作/拒绝 + 预算/代币统计 + prefill 数据 |
| P0-6 | 静态页面生成 | HTML 模板引擎生成：title/meta/canonical/H1/intro/examples/FAQ/internal-links，输出到 frontend/generated/ |
| P0-7 | SEO 页面注册表 | frontend/data/seo-pages.json，包含 slug/canonical_url/primary_keyword/canonical_group/intent/status/content_fingerprint 等字段 |
| P0-8 | 失败注册表 | frontend/data/seo-failures.json，记录被门禁拒绝的候选词及重试策略 |
| P0-9 | Sitemap 自动更新 | 基于 seo-pages.json 自动更新 frontend/sitemap.xml（含 lastmod/priority/changefreq） |
| P0-10 | 质量门禁 | 8 个 gate：relevance/duplicate-intent/helpful-content/spam/html-validity/build/cost-rate-limit/content-drift |
| P0-11 | 每日运行报告 | docs/seo-runs/YYYYMMDD-published.md 和 YYYYMMDD-failed-candidates.md |
| P0-12 | GitHub Actions 调度 | .github/workflows/seo-daily.yml，cron 00:00 Asia/Shanghai |
| P0-13 | LLM 成本/频率限制 | 每日 token 预算/成本预算/候选词上限/生成页面上限，超限自动停止 |
| P0-14 | Generator Prefill | 前端读取 #generator-prefill JSON，预填 generator 状态并显示 CTA |
| P0-15 | 内容漂移检测 | content_fingerprint (SHA-256) + 相似度阈值（title<0.85, meta<0.85, body<0.82, example<0.78, faq<0.80） |

### P1 — Phase 2（本次不交付，仅记录边界）

- Astro SSG 迁移
- Search Console 数据集成
- Canonical group memory
- FAQ JSON-LD 验证自动化
- 后端反馈导出为 SEO 信号
- Internal link graph optimizer

### P2 — Phase 3（本次不交付）

- 大规模程序化 SEO 模板
- 自动 pruning/noindex 建议
- 排名反馈闭环
- 内容漂移 dashboard
- 内容质量健康监控

## 功能边界（明确不做的事）

1. **不做 Astro 迁移** — Phase 1 使用当前静态 HTML 模板生成，直到满足 Astro 迁移触发条件（50 页/14 天/2 个模板/20% 共享布局变更）才进入 Phase 2。
2. **不做人工审批** — 全自动化流水线，质量门禁替代人工审核。
3. **不做 Search Console 集成** — Phase 1 无此数据源，使用 Google Trends + LLM 扩展作为唯一关键词输入。
4. **不做后端运行时 SEO** — SEO 页面必须以静态文件形式部署，不存入 SQLite，不依赖后端运行时渲染。
5. **不做隐藏文本/关键词堆砌/伪装** — 所有生成内容必须是可见的、对用户有用的。
6. **不做每日超过 1 个新页面** — Phase 1 限制：最多 1 个新页面/天，最多 10 个更新/天。
7. **不修改 backend API 现有端点** — SEO worker 是独立模块，不改变现有 /api/generate-prompt、/api/feedback、/api/health 等端点的行为。
8. **不触碰 .env / backend provider secrets / 运行时数据库文件** — SEO worker 不修改这些文件。

## 技术约束与交付形式

### 技术栈

| 组件 | 技术选型 | 理由 |
|------|---------|------|
| SEO Worker | Python 3.13 | 与后端一致，可共享 LLM 客户端 |
| LLM | DeepSeek API（主）/ MiMo API（备） | 复用现有 DEEPSEEK_* 环境变量 |
| 模板引擎 | Jinja2 | Python 生态标准，足够生成 HTML |
| 调度器 | GitHub Actions cron | scope 文档推荐首选 |
| 前端部署 | 纯静态文件（Cloudflare Pages/Vercel/Netlify/GitHub Pages） | 不进 Docker |
| 后端部署 | 仍用 Docker Compose（仅 backend 服务） | 保持现有架构 |
| 关键词数据 | Google Trends API + LLM fallback | Trends 为 alpha，需 fallback |
| 相似度计算 | TF-IDF + cosine similarity | 便宜可靠，Phase 1 不需要 embeddings |

### 交付形式

1. **Python 模块**: `dnd-prompt-forge/backend/seo_worker/` — 包含关键词发现、LLM 决策、内容生成、质量门禁、注册表管理等子模块
2. **GitHub Actions workflow**: `.github/workflows/seo-daily.yml`
3. **HTML 模板**: `dnd-prompt-forge/backend/seo_worker/templates/long_tail_page.html.j2`
4. **生成输出**: `dnd-prompt-forge/frontend/generated/*.html`
5. **注册表文件**: `dnd-prompt-forge/frontend/data/seo-pages.json`, `dnd-prompt-forge/frontend/data/seo-failures.json`
6. **运行报告**: `docs/seo-runs/YYYYMMDD-*.md`
7. **前端修改**: `dnd-prompt-forge/frontend/js/app.jsx` — 增加 generator-prefill 读取逻辑
8. **部署配置修改**: `docker-compose.yml` — 移除 frontend 服务；`dnd-prompt-forge/frontend/Dockerfile` — 标记废弃或删除
9. **Sitemap 更新**: `dnd-prompt-forge/frontend/sitemap.xml` — 由 worker 自动更新
10. **测试**: `dnd-prompt-forge/backend/tests/test_seo_*.py` — 覆盖 worker 核心逻辑

### 环境变量（新增）

```
SEO_LLM_DAILY_TOKEN_BUDGET=100000
SEO_LLM_DAILY_COST_BUDGET_USD=5.00
SEO_LLM_MAX_CANDIDATES_PER_RUN=100
SEO_LLM_MAX_GENERATED_PAGES_PER_RUN=1
SEO_LLM_MAX_UPDATED_PAGES_PER_RUN=10
SEO_LLM_MAX_RETRIES_PER_STEP=1
SEO_SEED_KEYWORDS_PATH=dnd-prompt-forge/backend/seo_worker/seed_keywords.txt
SEO_TRENDS_API_KEY=
SEO_BASE_URL=https://dndpromptforge.com
```

## 验收标准（可量化的 AC 列表）

### AC-1: 后端可运行
- `pytest dnd-prompt-forge/backend/tests/ -q` 至少能完成 collection（不再 ModuleNotFoundError）
- 7 个原有测试中至少 5 个 pass

### AC-2: 前端不部署到 Docker
- `docker compose config` 输出中不含 `frontend` service
- `dnd-prompt-forge/frontend/Dockerfile` 已删除或重命名为 `Dockerfile.deprecated`

### AC-3: SEO Worker 可执行
- `python -m dnd-prompt-forge.backend.seo_worker` 可独立运行（需环境变量）
- 单次运行产出：至少 1 个 `frontend/generated/*.html` 或 `seo-failures.json` 更新
- 单次运行产出：`docs/seo-runs/YYYYMMDD-published.md` 或 `docs/seo-runs/YYYYMMDD-failed-candidates.md`

### AC-4: LLM 决策合约符合规范
- LLM 输出 JSON 包含所有 scope 文档要求的字段：date, selected_keywords, rejected_keywords, estimated_llm_cost_usd, token_budget, ssg_target, data_model_action, prefill
- Worker 在缺少必需字段时拒绝 LLM 输出

### AC-5: 静态页面质量
- 生成的 HTML 包含：title, meta description, canonical, H1, intro, 3-8 examples, FAQ, internal links
- 生成的 HTML 无隐藏文本（display:none 的 keyword block）
- canonical URL 指向 `https://dndpromptforge.com/<slug>`
- 页面通过 W3C HTML 验证（无致命错误）

### AC-6: 注册表完整性
- `seo-pages.json` 中每个 published 页面包含所有必需字段：slug, canonical_url, primary_keyword, canonical_group, intent, status, created_at, updated_at, last_trend_score, last_helpful_content_score, source_keywords, related_pages, content_fingerprint
- `seo-failures.json` 中每个失败候选包含：keyword, failed_gate, reason, recommended_next_action, retry_after_days, retry_count

### AC-7: Sitemap 自动更新
- 运行 SEO worker 后 `sitemap.xml` 包含所有 seo-pages.json 中 status=published 的页面
- 每个 URL 有 lastmod、priority、changefreq
- 新增页面自动出现在 sitemap 中

### AC-8: 质量门禁生效
- relevance gate 拒绝非 DND/fantasy/prompt 相关关键词
- duplicate-intent gate 拒绝与已有 canonical group 重叠的页面
- helpful-content gate 拒绝无 examples 的页面
- spam gate 拒绝关键词密度异常/隐藏文本/近重复页面
- content-drift gate 拒绝超过相似度阈值的页面
- 被拒绝的候选写入 seo-failures.json

### AC-9: 成本限制
- 单次运行 LLM token 消耗不超过 SEO_LLM_DAILY_TOKEN_BUDGET
- 单次运行 LLM 成本不超过 SEO_LLM_DAILY_COST_BUDGET_USD
- 超过 50% token 预算用于候选分析时，停止内容生成

### AC-10: GitHub Actions 可触发
- `.github/workflows/seo-daily.yml` 存在且语法正确
- 可手动触发（workflow_dispatch）
- cron 设置为 00:00 Asia/Shanghai

### AC-11: Generator Prefill
- 访问 `https://dndpromptforge.com/dragonborn-paladin-token-prompt` 时，generator 自动预填 type=token, race=Dragonborn, class=Paladin 等
- 页面显示可见 CTA："Open this Dragonborn Paladin token prompt in the generator"
- prefill 数据来自页面内嵌 `<script type="application/json" id="generator-prefill">`

### AC-12: 内容漂移检测
- 生成的页面 content_fingerprint 存入 seo-pages.json
- 新页面与同 canonical_group 已有页面的相似度在阈值内
- 相似度校准文档存于 `docs/seo-runs/similarity-calibration-YYYYMMDD.md`

### AC-13: 每日运行报告
- 成功运行产出 `docs/seo-runs/YYYYMMDD-published.md`，包含：运行日期、候选词数量、选中词、生成页面、门禁通过率、LLM 成本、token 消耗
- 失败候选产出 `docs/seo-runs/YYYYMMDD-failed-candidates.md`，包含：每个被拒候选的 keyword/failed_gate/reason/recommended_next_action

### AC-14: 现有功能不退化
- 首页 generator 正常工作
- 现有 /about, /privacy, /terms, /contact 页面正常访问
- 现有 API 端点 /api/health, /api/generate-prompt 正常响应

## Sprint 规划建议

### Sprint 1（前置修复 + 架构搭建）— 预计 2 天

| 任务 | 依赖 | 产出 |
|------|------|------|
| S1-T1: 后端源码恢复（从 .pyc 提取或重写） | 无 | backend/main.py, models/, middleware/, services/, routers/ 恢复 |
| S1-T2: 修改 docker-compose.yml 移除 frontend | 无 | docker-compose.yml 仅含 backend |
| S1-T3: SEO Worker 项目骨架 | S1-T1 | seo_worker/ 目录结构 + __main__.py + 配置加载 |
| S1-T4: HTML 页面模板 | 无 | templates/long_tail_page.html.j2 |
| S1-T5: seo-pages.json + seo-failures.json schema | 无 | 空初始注册表文件 |

### Sprint 2（核心流水线）— 预计 3 天

| 任务 | 依赖 | 产出 |
|------|------|------|
| S2-T1: 关键词发现模块 | S1-T3 | seed_keywords.txt + trends_fetcher + llm_expander |
| S2-T2: LLM 决策合约模块 | S1-T3 | decision_contract.py + JSON schema 验证 |
| S2-T3: 内容生成模块 | S1-T3 + S1-T4 | page_generator.py + Jinja2 渲染 |
| S2-T4: 质量门禁模块 | S1-T3 | 8 个 gate 实现 |
| S2-T5: 注册表管理模块 | S1-T5 | registry.py（读写 seo-pages.json / seo-failures.json） |

### Sprint 3（集成 + 前端 + 部署）— 预计 2 天

| 任务 | 依赖 | 产出 |
|------|------|------|
| S3-T1: Worker 主流程编排 | S2-T1~T5 | pipeline.py 串起完整流水线 |
| S3-T2: Sitemap 自动更新 | S2-T5 | sitemap_updater.py |
| S3-T3: Generator Prefill 前端改造 | S1-T3 | app.jsx 增加 #generator-prefill 逻辑 |
| S3-T4: GitHub Actions workflow | S3-T1 | seo-daily.yml |
| S3-T5: 运行报告生成 | S3-T1 | report.py |
| S3-T6: 内容漂移检测 | S2-T4 + S2-T5 | drift_detector.py + calibration doc |

### Sprint 4（测试 + 验收 + 修复）— 预计 2 天

| 任务 | 依赖 | 产出 |
|------|------|------|
| S4-T1: SEO Worker 单元测试 | S3-T1 | test_seo_*.py |
| S4-T2: 端到端手动运行测试 | S3-T1~T6 | 完整运行报告 + 至少 1 个生成页面 |
| S4-T3: 验收 AC 逐项检查 | S4-T2 | 验收报告 |
| S4-T4: Bug 修复 + 现有功能回归 | S4-T3 | 修复代码 |

**总预计工期: 9 天**

## 风险识别

| 编号 | 风险 | 影响 | 缓解措施 |
|------|------|------|---------|
| R1 | 后端 .pyc 反编译不完整或失败 | 阻塞 S1-T1，影响原有 API 功能 | 备选方案：基于测试文件和 scope 文档重写后端模块，以 .pyc 为参考 |
| R2 | Google Trends API 无访问权限 | 关键词发现降级为 LLM-only | 已有 fallback 设计：LLM 扩展种子词 + 第三方关键词 API |
| R3 | LLM 生成内容质量不稳定 | 产出低质量页面，被 Google 降权 | 8 个质量门禁 + content drift 检测 + 每日 1 页限制 |
| R4 | SEO 页面被 Google 判定为低质量/垃圾内容 | 站点整体排名下降 | helpful-content gate + 无隐藏文本 + 回滚机制（每日独立 commit） |
| R5 | 前端从 Docker 剥离后部署方式不确定 | 影响交付和测试 | Phase 1 可先验证本地静态文件输出，部署目标后续确认 |
| R6 | GitHub Actions runner 无法访问 LLM API | 每日流水线失败 | 配置超时重试 + 指数退避 + 失败时写 partial run report |
| R7 | 相似度阈值初始值不准 | 误拒好页面或漏放重复页面 | 初始校准 + 25 页后重新校准 + 100 页后再次校准 |
| R8 | 前端 Babel standalone 无构建系统 | 难以做 tree-shaking/优化 generator-prefill 代码 | Phase 1 接受现状，prefill 逻辑用原生 DOM API 读取，不走构建 |

value_review_ref: docs/cognition/value-review.md