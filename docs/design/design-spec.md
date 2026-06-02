# SEO Autonomous Static Content System -- Phase 1 MVP Design Specification

**版本**: v1
**日期**: 2026-06-02
**作者**: product-designer
**状态**: Phase 2 设计产出

---

## 1. 设计系统审计

### 1.1 现有设计语言摘要

| 维度 | 实现 |
|------|------|
| 主题切换 | `theme-forge` (light) + `.dark` (charcoal workbench) |
| 主色调 | 黄铜/金色 (`--brass` / `--brass-hover` / `--brass-press`) |
| 辅色调 | 纠红 (`--crimson`) + 翠绿 (`--emerald`) |
| 背景层级 | `--bg` (parchment) / `--bg-band` / `--paper` / `--inset` |
| 文字层级 | `--ink` (primary) / `--ink-2` (secondary) / `--ink-3` (tertiary) |
| 字体系统 | Cormorant Garamond (serif, display) / Manrope (sans, body) / JetBrains Mono (mono, prompt) |
| 间距系统 | 4px 基数: `--s1`..`--s9` (4/8/12/16/24/32/48/64/96px) |
| 圆角 | `--r-sm:6px` / `--r-md:9px` / `--r-lg:12px` / `--r-xl:16px` / `--r-full:999px` |

### 1.2 SEO 页面复用策略

SEO 长尾页面复用现有 CSS 变量和布局类，不引入新 CSS 框架。新增样式写入 `frontend/css/seo-pages.css`。

| SEO 页面区块 | 复用现有 CSS 类 |
|-------------|----------------|
| 页面外壳 | `theme-forge texture-on accent-brass` |
| Header | `.hdr` / `.hdr-inner` / `.brand` / `.nav` |
| Hero intro | `.hero` / `.hero-bg` / `.hero-inner` / `.intro` / `.kicker` / `.lede` |
| Generator CTA | `.btn.primary` + 新组件 `.prefill-cta` |
| Examples 区 | `.band.alt` / `.wrap.section` / `.section-head` / `.grid.c3` / `.ex-card` |
| Prompt blocks | `.pblock` / `.pbody` / `.copy-btn` |
| FAQ 区 | `.faq` / `.faq-item` / `.faq-q` / `.faq-a` (静态展开) |
| Internal links | `.band.alt` / `.links-grid` |
| Footer | `.footer` / `.footer-inner` / `.legal` |

---

## 2. 业务逻辑建模

### 2.1 Generator Prefill 业务流

用户从 Google 到达 SEO 长尾页 → 页面含 #generator-prefill JSON → 解析 JSON → 显示定向 CTA → 用户点击 → 导航至首页 + URL 参数 → App 解析参数 → 预填 Generator 表单

### 2.2 SEO 页面生成流水线业务流

每日 cron → 关键词发现 → LLM 决策 → 内容生成 → 质量门禁 → 写入 HTML → 更新注册表 → 更新 sitemap → 生成报告 → Git commit → 部署

---

## 3. 交互规格说明

### 3.1 Generator Prefill CTA 规格

**组件名**: PrefillCTA
**HTML 元素**: `<section class="prefill-cta">`
**数据绑定**: 页面内嵌 `<script type="application/json" id="generator-prefill">` JSON

- JSON 必须包含至少 `type` 和 `race` 字段才显示定向 CTA
- CTA 链接: `href="/?type=token&race=Dragonborn&class=Paladin&style=painterly&mood=heroic&model=midjourney"`
- JSON 字段 `klass` 映射为 URL 参数 `class`

视觉规格:
- 背景: `var(--paper)` + `border: 1px solid var(--line)`
- 圆角: `var(--r-lg)` = 12px
- 标题: Cormorant Garamond serif, `font: var(--t-h3)`
- CTA 按钮: `.btn.primary.lg`

新增 CSS:
```css
.prefill-cta {
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: var(--r-lg);
  padding: var(--s6) var(--s5);
  max-width: 560px;
  margin: var(--s6) auto;
  text-align: center;
  box-shadow: var(--shadow-sm);
}
.prefill-cta .cta-title {
  font: var(--t-h3);
  font-family: var(--serif);
  margin-bottom: var(--s3);
}
.prefill-cta .cta-tags {
  font: var(--t-label);
  letter-spacing: .06em;
  text-transform: uppercase;
  color: var(--brass-fg);
  margin-bottom: var(--s5);
}
.prefill-cta .cta-tags span {
  background: var(--brass-soft);
  padding: 3px 9px;
  border-radius: var(--r-sm);
  margin: 0 4px;
}
```

### 3.2 SEO 长尾页面布局规格

页面结构: Header → Hero(H1+intro+PrefillCTA) → Examples → How to use → Negative guidance → Related types → FAQ → Internal links → Footer

- H1 必须在 first viewport 可见
- Examples 数量: 3-8 个
- FAQ 为静态展开（无 JS toggle），对 Google crawler 友好
- CopyButton 用纯 HTML + `navigator.clipboard.writeText()`

### 3.3 SEO 页面模板变体

| 区块 | tool_page | race_class_page | model_guide | how_to_guide | example_gallery |
|------|-----------|-----------------|-------------|--------------|----------------|
| H1 | "DND [Type] Prompt Generator" | "[Race] [Class] [Type] Prompt Generator" | "[Model] DND Prompt Guide" | "How to Write DND [Topic] Prompts" | "DND [Topic] Prompt Examples" |
| Examples 数量 | 5-8 | 3-6 | 3-5 | 2-4 | 8-12 |

单一 Jinja2 模板 `long_tail_page.html.j2`，通过 `page_intent` 参数控制条件渲染。

---

## 4. UI 状态矩阵

### 4.1 Generator Prefill 状态

| 状态 | 上下文 | 视觉表现 |
|------|--------|---------|
| No Prefill | 直接访问首页 | Generator 默认空状态 |
| Prefill Available (URL params) | 从 SEO 页面 CTA 到首页 | Generator 表单预填 |
| Prefill Available (embedded JSON) | SEO 页面内嵌 JSON | PrefillCTA 区块可见 |
| Prefill Incomplete | JSON 缺少 type/race | Fallback CTA "Try the DND prompt generator" |

### 4.2 Prefill 字段映射

| prefill JSON 字段 | Generator 表单字段 | URL query 参数名 |
|-------------------|-------------------|-----------------|
| `type` | `form.type` | `type` |
| `race` | `form.race` | `race` |
| `klass` | `form.klass` | `class` |
| `style` | `form.style` | `style` |
| `mood` | `form.mood` | `mood` |
| `model` | `form.model` | `model` |

---

## 5. 无障碍检查

- 所有 `<a>` 和 `<button>` 有描述性文字或 `aria-label`
- 全局 `:focus-visible` 样式: `2px solid var(--focus)`
- `<h1>` → `<h2>` → `<h3>` 严格层级不跳级
- FAQ 用 `<h3>` + `<div role="region" aria-labelledby="...">`，静态展开
- JSON-LD FAQPage 必须与可见 FAQ 完全匹配
- CopyButton 成功后用 inline 文案 "Copied" + `aria-live="polite"`

---

## 6. 首页 Generator Prefill 前端改造

### app.jsx 改造

新增 `prefill` 状态，mount 时解析 `window.location.search` 参数，映射为 Generator 表单初始值。

### generator.jsx 改造

新增 `prefill` prop，mount 时合并到 `form` 状态。

---

## 7. Jinja2 模板数据模型

```python
page_data = {
  "slug": "dragonborn-paladin-token-prompt",
  "canonical_url": "https://dndpromptforge.com/dragonborn-paladin-token-prompt",
  "primary_keyword": "dragonborn paladin token prompt",
  "page_intent": "race_class_page",
  "title": "Dragonborn Paladin Token Prompt Generator | DND Prompt Forge",
  "meta_description": "...",
  "h1": "Dragonborn Paladin Token Prompt Generator",
  "intro": "...",
  "prefill": {"type": "token", "race": "Dragonborn", "klass": "Paladin", ...},
  "examples": [{"badge": "Token", "name": "...", "positive": "...", "negative": "..."}],
  "faqs": [{"question": "...", "answer": "..."}],
  "internal_links": [{"label": "...", "href": "..."}],
  "generated_date": "2026-06-03"
}
```
