# AdSense Low-Value Content Remediation — Design Specification

## 设计系统审计结果

**框架**：纯 React 18 + 自定义 CSS 变量（无 Tailwind/AntD/MUI/shadcn）
**设计风格**："Practical fantasy workshop" — warm parchment `#F4EEDF`, brass primary `#9A6E22`, crimson/emerald accents
**字体**：Cormorant Garamond (serif) / Manrope (sans) / JetBrains Mono (mono)
**间距系统**：4px 基数（`--s1` 到 `--s9`，即 4px 到 96px）
**现有组件**：Button, Field, Segmented, Select, CopyButton, Collapse, Toast, Icon (lucide)
**页面架构**：SPA 首页（React `#app` 挂载）+ 静态 HTML 页面（`pages/*.html`，Nginx 直接服务）
**导航**：Header `NAV` 常量（6 项）+ Footer 4 列（Brand / Generators / Site / Extra tools）

**关键约束**：指南页面必须是静态 HTML 文件（与 `about.html` 同模式），因为 React SPA 不路由这些路径。Nginx 需为每个指南页添加 `location` 块。

---

## 1. 业务逻辑建模

### 1.1 数据约束

| 字段 | 约束 | 说明 |
|------|------|------|
| guide slug | 格式 `dnd-{type}-prompt-guide`，type ∈ {character, token, monster, npc, scene} | 路由后缀 |
| guide title | 非空，≤ 80 chars | SEO title |
| guide description | 非空，≤ 160 chars | Meta description |
| guide canonical | `https://dnd.whatai.me/{slug}` | 唯一规范 URL |
| guide content | 7 个必需区块，每区块 ≥ 100 words | 内容深度要求 |
| contact email | `support@dnd.whatai.me` | 替换假表单 |

### 1.2 业务规则

- **指南页面不加载 AdSense 脚本**（属于非内容页面类别，直到内容审核通过后才考虑）
- **首页卡片链接指向静态 HTML 页面**，不走 React SPA 路由
- **页脚指南链接使用 `<a href>` 而非 `onClick + onNav`**，因为是跨页面导航
- **Contact 页面不再有表单提交逻辑**，仅展示邮箱地址
- **5 个指南页面必须在 sitemap 中列出**
- **每个指南页面必须有独立的 canonical URL、title、meta description、OG tags**

### 1.3 指南页面 7 个内容区块

来源：诊断文档 "Content development requirement" 章节

| # | 区块 | 内容要求 | 视觉层次 |
|---|------|----------|----------|
| 1 | When to use this prompt type | 使用场景和时机 | h2 + prose |
| 2 | Composition decisions & trade-offs | 构图决策与取舍 | h2 + prose + callout boxes |
| 3 | Before/after examples | 完整的修改前后对比 | h2 + paired prompt blocks |
| 4 | Common failure patterns & corrections | 常见失败模式及修正 | h2 + warning banners + code |
| 5 | Model-specific guidance | 按模型分别指导 | h2 + tab-like sections |
| 6 | Reviewed prompt template | 人工审核的模板 | h2 + prompt block (mono) |
| 7 | FAQs + related links | FAQ + 内链到其他指南和生成器 | h2 + accordion + link grid |

---

## 2. 全路径业务流

```mermaid
graph TD
    A[User lands on homepage] --> B{Scroll past generator?}
    B -- No --> C[Uses generator tool]
    B -- Yes --> D[Sees Guide Cards section]
    D --> E{Clicks guide card?}
    E -- Yes --> F[Static HTML guide page loads]
    E -- No --> G[Scrolls to FAQ / Footer]
    G --> H{Clicks footer guide link?}
    H -- Yes --> F
    H -- No --> I[Other navigation]

    F --> J[User reads guide content]
    J --> K{Clicks "Try the generator" CTA?}
    K -- Yes --> L[Returns to homepage /#generator]
    K -- No --> M{Clicks related guide link?}
    M -- Yes --> N[Another guide page loads]
    M -- No --> O[User leaves or bookmarks]

    P[User visits /contact] --> Q[Sees email address, no form]
    Q --> R{Clicks mailto link?}
    R -- Yes --> S[Email client opens]
    R -- No --> T[Browses other pages]
```

---

## 3. 首页卡片导航设计

### 3.1 位置

在现有 `PromptGuide` 区块（"One tool, six outputs"）和 `HowItWorks` 区块之间插入新 section。理由：
- 位于生成器工具下方，不干扰主工具使用
- 在 "How it works" 上方，逻辑上从 "6 种输出类型" 自然延伸到 "深入学习每种类型"
- 与现有 `PromptGuide` 的 `guide-card` 视觉模式一致，但链接到独立页面而非仅展示摘要

### 3.2 区块结构

**Section 名称**：`GuideCards`（在 `content-sections.jsx` 中新增）

**视觉设计**：使用现有 `.band.alt`（交替背景色）+ `.wrap.section` + `.grid.c3` 布局，与 `Examples` 区块同模式。

**5 张卡片数据**：

```javascript
const GUIDE_PAGES = [
  {
    id: 'character',
    icon: 'user',
    title: 'Character portrait prompts',
    excerpt: 'When to use portraits, composition choices, before/after examples, and model-specific tips for DND character art.',
    href: '/dnd-character-prompt-guide',
  },
  {
    id: 'token',
    icon: 'circle-dot',
    title: 'VTT token prompts',
    excerpt: 'Top-down token composition, clean silhouettes, transparent backgrounds, and export settings for virtual tabletops.',
    href: '/dnd-token-prompt-guide',
  },
  {
    id: 'monster',
    icon: 'skull',
    title: 'Monster & creature prompts',
    excerpt: 'Scale cues, anatomy emphasis, threatening presence, and environment integration for DND monster art.',
    href: '/dnd-monster-prompt-guide',
  },
  {
    id: 'npc',
    icon: 'users',
    title: 'NPC portrait prompts',
    excerpt: 'Role-defining traits, memorable details, approachable framing, and quick in-world NPC generation.',
    href: '/dnd-npc-prompt-guide',
  },
  {
    id: 'scene',
    icon: 'mountain',
    title: 'Fantasy scene prompts',
    excerpt: 'Establishing shots, depth layers, encounter hooks, and atmospheric lighting for DND location art.',
    href: '/dnd-scene-prompt-guide',
  },
];
```

### 3.3 卡片 HTML 结构

复用现有 `.guide-card` 样式，增加链接行为：

```html
<article class="guide-card">
  <div class="gi"><i data-lucide="user"></i></div>
  <h3>Character portrait prompts</h3>
  <p>When to use portraits, composition choices…</p>
  <a href="/dnd-character-prompt-guide" class="guide-link">
    Read the guide <i data-lucide="arrow-right" style="width:14px;height:14px;"></i>
  </a>
</article>
```

### 3.4 新增 CSS

```css
/* Guide link inside guide-card */
.guide-card .guide-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font: var(--t-small);
  font-weight: 600;
  color: var(--brass-fg);
  margin-top: var(--s3);
  transition: color var(--dur);
}
.guide-card .guide-link:hover {
  color: var(--brass-hover);
}
.guide-card .guide-link i {
  transition: transform var(--dur) var(--ease);
}
.guide-card .guide-link:hover i {
  transform: translateX(3px);
}
```

### 3.5 响应式布局

- 桌面（> 860px）：3 列网格（`.grid.c3`），5 张卡片自然流动（3 + 2）
- 平板（600-860px）：2 列网格
- 移动（< 600px）：1 列堆叠

### 3.6 Section Head

```
kicker: "Learn the craft"
title: "DND prompt guides"
body: "Deep dives into each prompt type — when to use it, how to compose it, and what to watch out for."
```

---

## 4. 页脚指南区块设计

### 4.1 位置

在现有 4 列页脚中，将 "指南" 列插入 "生成器" 和 "站点" 之间。页脚变为 5 列：

| 列 | 内容 | 宽度 |
|----|------|------|
| Brand | 品牌描述 | 1.6fr |
| Generators | 5 个生成器链接 | 1fr |
| **指南** | **5 个指南链接** | **1fr** |
| Site | About/Contact/Privacy/Terms | 1fr |
| Extra tools | Excel converter | 1fr |

### 4.2 数据结构

```javascript
const FOOTER_GUIDES = [
  { label: 'Character guide', href: '/dnd-character-prompt-guide' },
  { label: 'Token guide', href: '/dnd-token-prompt-guide' },
  { label: 'Monster guide', href: '/dnd-monster-prompt-guide' },
  { label: 'NPC guide', href: '/dnd-npc-prompt-guide' },
  { label: 'Scene guide', href: '/dnd-scene-prompt-guide' },
];
```

### 4.3 JSX 结构

```jsx
<div className="fcol">
  <h4>Guides</h4>
  <ul>{FOOTER_GUIDES.map(g => (
    <li key={g.href}><a href={g.href}>{g.label}</a></li>
  ))}</ul>
</div>
```

**关键**：使用 `<a href>` 而非 `<a onClick={onNav}>`，因为指南页面是静态 HTML，不在 SPA 路由内。

### 4.4 CSS 调整

页脚网格从 4 列改为 5 列：

```css
.footer-inner {
  grid-template-columns: 1.6fr 1fr 1fr 1fr 1fr;
}
@media (max-width: 760px) {
  .footer-inner { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 440px) {
  .footer-inner { grid-template-columns: 1fr; }
}
```

---

## 5. 指南页面设计

### 5.1 页面模板结构

每个指南页面是独立静态 HTML 文件，遵循 `about.html` 的模式：

```
frontend/pages/dnd-character-prompt-guide.html
frontend/pages/dnd-token-prompt-guide.html
frontend/pages/dnd-monster-prompt-guide.html
frontend/pages/dnd-npc-prompt-guide.html
frontend/pages/dnd-scene-prompt-guide.html
```

### 5.2 HTML 骨架

以 character guide 为例：

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>DND Character Portrait Prompt Guide | DND Prompt Forge</title>
  <meta name="description" content="Learn when to use character portrait prompts, composition choices, before/after examples, and model-specific tips for DND art." />
  <link rel="canonical" href="https://dnd.whatai.me/dnd-character-prompt-guide" />
  <meta property="og:title" content="DND Character Portrait Prompt Guide | DND Prompt Forge" />
  <meta property="og:description" content="Learn when to use character portrait prompts, composition choices, and model-specific tips for DND art." />
  <meta property="og:type" content="article" />
  <meta property="og:url" content="https://dnd.whatai.me/dnd-character-prompt-guide" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="../css/style.css" />
  <!-- NO AdSense script — guide pages are not monetized yet -->
</head>
<body>
  <div class="wrap" style="padding-top: var(--s8);">
    <div class="prose">
      <!-- Page header -->
      <div class="guide-header">
        <a href="/" class="guide-back">
          <i data-lucide="arrow-left" style="width:16px;height:16px;"></i>
          Back to generator
        </a>
      </div>
      <h1>DND Character Portrait Prompt Guide</h1>
      <div class="updated">Guide · last updated June 2026</div>
      <p class="lede">[Opening paragraph — what this guide covers and who it's for]</p>

      <!-- Section 1: When to use -->
      <h2>When to use character portrait prompts</h2>
      <p>…</p>

      <!-- Section 2: Composition decisions -->
      <h2>Composition decisions and trade-offs</h2>
      <p>…</p>
      <div class="guide-callout">…</div>

      <!-- Section 3: Before/after examples -->
      <h2>Before and after examples</h2>
      <div class="guide-comparison">
        <div class="guide-before">…</div>
        <div class="guide-after">…</div>
      </div>

      <!-- Section 4: Common failures -->
      <h2>Common failure patterns and corrections</h2>
      <div class="guide-warning">…</div>

      <!-- Section 5: Model-specific guidance -->
      <h2>Model-specific guidance</h2>
      <h3>Midjourney</h3>
      <p>…</p>
      <h3>ChatGPT / DALL-E</h3>
      <p>…</p>
      <h3>Stable Diffusion</h3>
      <p>…</p>

      <!-- Section 6: Reviewed template -->
      <h2>Reviewed prompt template</h2>
      <div class="guide-template">…</div>

      <!-- Section 7: FAQ + related -->
      <h2>Frequently asked questions</h2>
      <div class="guide-faq">…</div>

      <!-- CTA: Try the generator -->
      <div class="guide-cta">
        <a href="/" class="btn primary">Try the character prompt generator</a>
      </div>

      <!-- Related guides -->
      <h2>Related guides</h2>
      <div class="guide-related">
        <a href="/dnd-token-prompt-guide">VTT token prompt guide</a>
        <a href="/dnd-npc-prompt-guide">NPC portrait prompt guide</a>
        <a href="/dnd-monster-prompt-guide">Monster prompt guide</a>
        <a href="/dnd-scene-prompt-guide">Fantasy scene prompt guide</a>
      </div>
    </div>
  </div>
  <script src="https://unpkg.com/lucide@latest/dist/umd/lucide.min.js"></script>
  <script>lucide.createIcons();</script>
</body>
</html>
```

### 5.3 7 个内容区块的视觉层次

| 区块 | 视觉处理 | CSS 类 |
|------|----------|--------|
| 1. When to use | 标准 prose 段落 | `.prose h2 + p` |
| 2. Composition decisions | 段落 + callout boxes | `.prose h2 + p + .guide-callout` |
| 3. Before/after examples | 并排对比块 | `.guide-comparison > .guide-before + .guide-after` |
| 4. Common failures | 警告 banner + 代码块 | `.guide-warning + .guide-code` |
| 5. Model-specific guidance | h3 子标题分段 | `.prose h2 + h3 + p` |
| 6. Reviewed template | mono 字体代码块 | `.guide-template` |
| 7. FAQ + related | 简单问答 + 链接网格 | `.guide-faq + .guide-related` |

### 5.4 新增 CSS（指南页面专用）

```css
/* Guide page specific styles */
.guide-header {
  margin-bottom: var(--s5);
}
.guide-back {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font: var(--t-small);
  font-weight: 600;
  color: var(--ink-2);
  transition: color var(--dur);
}
.guide-back:hover {
  color: var(--brass-fg);
}

/* Callout box (composition tips) */
.guide-callout {
  background: var(--brass-soft);
  border: 1px solid var(--brass-line);
  border-left: 3px solid var(--brass);
  border-radius: var(--r-md);
  padding: var(--s4);
  margin: var(--s4) 0;
  font: var(--t-small);
  color: var(--ink-2);
  line-height: 1.6;
}

/* Before/after comparison */
.guide-comparison {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--s4);
  margin: var(--s5) 0;
}
@media (max-width: 600px) {
  .guide-comparison { grid-template-columns: 1fr; }
}
.guide-before,
.guide-after {
  background: var(--inset);
  border: 1px solid var(--line);
  border-radius: var(--r-md);
  padding: var(--s4);
}
.guide-before h4,
.guide-after h4 {
  font: var(--t-label);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--ink-3);
  margin-bottom: var(--s2);
}
.guide-before pre,
.guide-after pre {
  font: var(--t-mono);
  white-space: pre-wrap;
  word-break: break-word;
  color: var(--ink-2);
  margin: 0;
}
.guide-before { border-color: var(--crimson-soft); }
.guide-after { border-color: var(--emerald-soft); }

/* Warning box (failure patterns) */
.guide-warning {
  background: var(--crimson-soft);
  border: 1px solid color-mix(in oklab, var(--crimson) 30%, transparent);
  border-radius: var(--r-md);
  padding: var(--s4);
  margin: var(--s4) 0;
  font: var(--t-small);
  color: var(--crimson-fg);
  line-height: 1.6;
}

/* Code block (corrections) */
.guide-code {
  background: var(--inset);
  border: 1px solid var(--line);
  border-radius: var(--r-md);
  padding: var(--s4);
  margin: var(--s4) 0;
  font: var(--t-mono);
  color: var(--ink-2);
  white-space: pre-wrap;
  word-break: break-word;
}

/* Prompt template block */
.guide-template {
  background: var(--inset);
  border: 1px solid var(--brass-line);
  border-radius: var(--r-md);
  padding: var(--s5);
  margin: var(--s5) 0;
  font: var(--t-mono);
  font-size: 14px;
  line-height: 1.7;
  color: var(--ink);
  white-space: pre-wrap;
  word-break: break-word;
}

/* FAQ section */
.guide-faq {
  margin: var(--s5) 0;
}
.guide-faq-q {
  font-weight: 700;
  font-family: var(--serif);
  font-size: 18px;
  color: var(--ink);
  margin-bottom: var(--s2);
}
.guide-faq-a {
  font: var(--t-body);
  font-size: 15px;
  color: var(--ink-2);
  line-height: 1.6;
}

/* CTA block */
.guide-cta {
  margin: var(--s7) 0;
  padding: var(--s5);
  background: var(--brass-soft);
  border: 1px dashed var(--brass-line);
  border-radius: var(--r-md);
  text-align: center;
}

/* Related guides */
.guide-related {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--s3);
  margin: var(--s4) 0;
}
@media (max-width: 600px) {
  .guide-related { grid-template-columns: 1fr; }
}
.guide-related a {
  display: flex;
  align-items: center;
  gap: 8px;
  font: var(--t-small);
  font-weight: 600;
  color: var(--ink-2);
  padding: var(--s3);
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: var(--r-md);
  transition: border-color var(--dur), color var(--dur);
}
.guide-related a:hover {
  border-color: var(--brass-line);
  color: var(--brass-fg);
}
```

### 5.5 内链导航

每个指南页面底部包含：

1.  **CTA 按钮**：`Try the {type} prompt generator` — 链接到 `/?type={type_value}`（首页 + prefill 参数）
2.  **Related guides**：链接到其他 4 个指南页面（排除当前页面）
3.  **返回链接**：页面顶部 `Back to generator` 链接到 `/`

内链映射表：

| 指南页面 | CTA 链接 | 关联指南 |
|-----------|----------|----------|
| character | `/?type=portrait` | token, npc, monster, scene |
| token | `/?type=token` | character, npc, monster, scene |
| monster | `/?type=monster` | character, token, npc, scene |
| npc | `/?type=npc` | character, token, monster, scene |
| scene | `/?type=scene` | character, token, monster, npc |

### 5.6 移动端适配

- `.prose` 容器已有 `max-width: 720px` + `padding: var(--s8) var(--s5)`，移动端自然适配
- `.guide-comparison` 在 < 600px 时从 2 列变为 1 列堆叠
- `.guide-related` 在 < 600px 时从 2 列变为 1 列
- 所有文字使用 `clamp()` 或相对单位，无需额外断点
- CTA 按钮使用 `.btn.primary`，默认 42px 高度，触摸友好

---

## 6. Contact 页面改造设计

### 6.1 设计目标

将假表单替换为诚实的邮箱联系方式，保持 `.prose` 布局和整体风格一致性。

### 6.2 静态 HTML 版本（`pages/contact.html`）

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <!-- same head as before, minus AdSense script -->
  <title>Contact | DND Prompt Forge</title>
  <meta name="description" content="Contact DND Prompt Forge — reach us by email for feedback, bug reports, and feature requests." />
  <link rel="canonical" href="https://dnd.whatai.me/contact" />
  <!-- OG tags, fonts, style.css — NO AdSense -->
</head>
<body>
  <div class="wrap" style="padding-top: var(--s8);">
    <div class="prose">
      <h1>Contact</h1>
      <div class="updated">We usually reply within a couple of days.</div>
      <p class="lede">Feedback on the prompts, a bug, or a prompt type you wish existed? Send it over.</p>

      <div class="contact-method">
        <div class="contact-icon">
          <i data-lucide="mail" style="width:24px;height:24px;"></i>
        </div>
        <div>
          <h2>Email us</h2>
          <a href="mailto:support@dnd.whatai.me" class="contact-email">
            support@dnd.whatai.me
          </a>
          <p class="contact-note">For prompt feedback, bug reports, or feature ideas. We read every message.</p>
        </div>
      </div>

      <div style="margin-top: var(--s6);">
        <a href="/" class="btn secondary">Back to generator</a>
      </div>
    </div>
  </div>
  <script src="https://unpkg.com/lucide@latest/dist/umd/lucide.min.js"></script>
  <script>lucide.createIcons();</script>
</body>
</html>
```

### 6.3 React 组件版本（`prose-pages.jsx` 中的 `Contact`）

```jsx
const Contact = () => (
  <div className="prose">
    <h1>Contact</h1>
    <div className="updated">We usually reply within a couple of days.</div>
    <p className="lede">Feedback on the prompts, a bug, or a prompt type you wish existed? Send it over.</p>
    <div className="contact-method">
      <div className="contact-icon">
        <Icon name="mail" size={24} />
      </div>
      <div>
        <h2>Email us</h2>
        <a href="mailto:support@dnd.whatai.me" className="contact-email">
          support@dnd.whatai.me
        </a>
        <p className="contact-note">For prompt feedback, bug reports, or feature ideas. We read every message.</p>
      </div>
    </div>
  </div>
);
```

### 6.4 新增 CSS

```css
/* Contact method block */
.contact-method {
  display: flex;
  gap: var(--s4);
  align-items: flex-start;
  margin-top: var(--s5);
  padding: var(--s5);
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: var(--r-lg);
}
.contact-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--r-md);
  background: var(--brass-soft);
  color: var(--brass-fg);
  display: grid;
  place-items: center;
  flex: none;
}
.contact-method h2 {
  font: var(--t-h3);
  font-family: var(--serif);
  font-size: 20px;
  margin-bottom: var(--s2);
}
.contact-email {
  font: var(--t-body);
  font-size: 18px;
  font-weight: 600;
  color: var(--brass-fg);
  transition: color var(--dur);
}
.contact-email:hover {
  color: var(--brass-hover);
}
.contact-note {
  font: var(--t-small);
  color: var(--ink-3);
  margin-top: var(--s2);
}
```

### 6.5 状态矩阵

| 状态 | 表现 | 说明 |
|------|------|------|
| Default | 邮箱链接可见，brass 色 | 正常态 |
| Hover | 邮箱链接变 `--brass-hover` 色 | 交互反馈 |
| Focus | `focus-visible` outline | 键盘可达 |
| Visited | 保持 brass 色（不区分 visited） | 视觉一致 |
| Mobile | `.contact-method` 纵向堆叠 | < 420px |

---

## 7. UI 状态矩阵

### 7.1 首页指南卡片

| 状态 | 卡片 | 链接 | 说明 |
|------|------|------|------|
| Default | `.guide-card` 默认样式 | brass 色 | 正常态 |
| Hover | 卡片 `border-color: var(--brass-line)` + `translateY(-2px)` | 箭头右移 3px | 交互反馈 |
| Focus | `focus-visible` outline on link | — | 键盘可达 |
| Loading | N/A | N/A | 静态内容，无 loading |
| Empty | 不渲染 section | — | 无指南数据时隐藏 |
| Error | N/A | N/A | 静态内容，无 error |

### 7.2 页脚指南链接

| 状态 | 表现 | 说明 |
|------|------|------|
| Default | `var(--ink-2)` 色 | 与其他页脚链接一致 |
| Hover | `var(--ink)` 色 | 与其他页脚链接一致 |
| Focus | `focus-visible` outline | 键盘可达 |

### 7.3 指南页面

| 状态 | 表现 | 说明 |
|------|------|------|
| Default | 完整 7 区块内容 | 正常态 |
| Loading | N/A | 静态 HTML，无 loading |
| Error | N/A | 静态 HTML，无 JS 错误态 |
| Mobile | 单列布局，comparison 堆叠 | 响应式 |

---

## 8. 无障碍 (A11y)

- 所有指南卡片链接使用语义化 `<a href>` 而非 `<div onclick>`
- 页脚指南链接使用 `<a href>` 原生导航
- 邮箱链接使用 `<a href="mailto:...">` 原生行为
- 图标使用 `aria-hidden="true"`（lucide 默认）
- 指南页面保持 `h1 > h2 > h3` 标题层级，不跳级
- Before/after 对比块使用 `h4` 标签区分
- 颜色对比度：brass-fg `#7A5512` on parchment `#F4EEDF` = 4.6:1（AA 通过）
- Contact 邮箱图标容器有 `place-items:center` 对齐

---

## 9. 响应式断点总结

| 断点 | 首页卡片 | 页脚 | 指南页 | Contact |
|------|----------|------|--------|---------|
| > 860px | 3 列 | 5 列 | prose 720px | 横向 contact-method |
| 600-860px | 2 列 | 2 列 | prose 720px | 横向 contact-method |
| 420-600px | 1 列 | 1 列 | prose 全宽 | 横向 contact-method |
| < 420px | 1 列 | 1 列 | prose 全宽 | 纵向堆叠 contact-method |

---

## 10. 需修改的文件清单

| 文件 | 修改类型 | 说明 |
|------|----------|------|
| `frontend/src/legacy-app.jsx` | 修改 | 新增 `GuideCards` 组件 + `FOOTER_GUIDES` 常量 + Footer 5 列 + Contact 组件重写 |
| `frontend/css/style.css` | 修改 | 新增指南页面 CSS + Contact CSS + 页脚 5 列 + guide-link 样式 |
| `frontend/pages/dnd-character-prompt-guide.html` | 新增 | 静态 HTML 指南页 |
| `frontend/pages/dnd-token-prompt-guide.html` | 新增 | 静态 HTML 指南页 |
| `frontend/pages/dnd-monster-prompt-guide.html` | 新增 | 静态 HTML 指南页 |
| `frontend/pages/dnd-npc-prompt-guide.html` | 新增 | 静态 HTML 指南页 |
| `frontend/pages/dnd-scene-prompt-guide.html` | 新增 | 静态 HTML 指南页 |
| `frontend/pages/contact.html` | 修改 | 移除假表单，替换为邮箱 |
| `deploy/nginx.conf` | 修改 | 新增 5 个指南页 `location` 块 |
| `frontend/scripts/verify-build.mjs` | 修改 | 新增 5 个指南页的构建验证（无 AdSense 检查） |
| `frontend/scripts/copy-static.mjs` | 可能修改 | 确保指南页 HTML 复制到 dist |

---

## 11. 架构师关注点

1.  **Nginx 路由**：5 个新 `location` 块，模式 `location = /dnd-{type}-prompt-guide { try_files /pages/dnd-{type}-prompt-guide.html =404; }`，加 trailing-slash 301 重定向
2.  **Sitemap 更新**：5 个新 canonical URL 需加入 sitemap.xml
3.  **构建验证**：`verify-build.mjs` 需确认指南页 HTML 存在且不含 AdSense 脚本
4.  **静态文件复制**：`copy-static.mjs` 需确保 `pages/*.html` 包含新指南页
5.  **React SPA Contact 组件**：移除表单状态管理（`useState` for form/errors/sent），简化为纯展示组件，减少 bundle 大小
6.  **首页 `GuideCards` 组件**：在 `content-sections.jsx` 中新增，插入 `Home` fragment 的 `PromptGuide` 和 `HowItWorks` 之间
7.  **Footer 列数变化**：CSS grid 从 4 列改为 5 列，需验证移动端断点不破坏
8.  **内链预填充**：指南页 CTA 链接 `/?type=portrait` 依赖现有 `parsePrefillFromURL()` 逻辑，需确认 `type` 参数映射正确
9.  **Lucide 图标**：静态 HTML 页面需加载 lucide UMD 脚本（`<script src="unpkg.com/lucide">`），或改用内联 SVG 避免外部依赖
