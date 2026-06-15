# AdSense Low-Value Content Remediation — Architecture Specification

## 0. Meta

| Field | Value |
|-------|-------|
| Feature | AdSense Low-Value Content Remediation |
| Project | DND Prompt Forge (dnd.whatai.me) |
| Sprint Count | 2 |
| Architect | architect agent |
| Date | 2026-06-14 |
| Status | Phase 2 — Technical Contract |

---

## 1. ADR-1: Static HTML Guide Pages over React SPA Routes

- **Background**: The site is a React SPA with static HTML fallback pages for legal/about/contact. Adding 5 content guide pages could be done either as React components (rendered inside the SPA) or as standalone static HTML pages (like the existing `pages/*.html`).
- **Decision**: Use standalone static HTML pages in `frontend/pages/`, served by Nginx with clean URL routing (identical pattern to existing `/about`, `/privacy`, etc.).
- **Rationale**:
  - The existing legal/about/contact pages already use this pattern and it works.
  - Static HTML pages are independently crawlable by Googlebot without JavaScript rendering — critical for AdSense approval and SEO.
  - Each guide page has unique `<title>`, `<meta description>`, `<link rel="canonical">`, and JSON-LD — all visible to crawlers without JS execution.
  - React SPA routes would require Googlebot to execute JavaScript to see content, and the AdSense script in `index.html` would be loaded on all SPA routes regardless.
  - The guide pages are long-form editorial content that does not need React interactivity.
- **Risk**: Guide pages are not part of the React bundle, so they cannot share React components (Header, Footer). They will use a simple HTML footer with hardcoded links instead. This is acceptable because these pages are editorial, not interactive.

---

## 2. ADR-2: AdSense Script Placement Policy

- **Background**: Currently AdSense script is in `<head>` of all 5 pages (index.html + 4 legal pages). verify-build.mjs enforces this.
- **Decision**: AdSense script shall be present ONLY in `index.html` (the SPA/tool page) and the 5 new guide pages. It shall be ABSENT from about, contact, privacy, terms, and excel-ratio-converter pages. verify-build.mjs shall enforce this split.
- **Rationale**: Google AdSense policy prohibits ads on pages that are primarily navigational, legal, or action-oriented. The new guide pages are original publisher content and are appropriate for ad monetization.
- **Risk**: The SPA architecture means that navigating from the homepage (which has AdSense) to /about via React Router will not unload the AdSense script. This is mitigated by the Nginx routing: clean URLs like `/about` serve their own static HTML (not the SPA), so a full page load occurs and the AdSense script is not present.

---

## 3. Sprint 1: Infrastructure Fix + Legal Page Cleanup

### 3.1 AdSense Script Removal — Exact Locations

The AdSense script tag to remove is:
```html
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-9123849728110588"
    crossorigin="anonymous"></script>
```

| File | Action |
|------|--------|
| `pages/about.html` | Remove AdSense `<script>` from `<head>` |
| `pages/contact.html` | Remove AdSense `<script>` from `<head>` |
| `pages/privacy.html` | Remove AdSense `<script>` from `<head>` |
| `pages/terms.html` | Remove AdSense `<script>` from `<head>` |

**Do NOT modify** `index.html` — it retains the AdSense script.

### 3.2 Contact Page Replacement — Static HTML

Replace the entire `<body>` content of `pages/contact.html` with email-only content:
- Remove the `<form>` element entirely
- Add a `mailto:support@whatai.me` link using `.btn.primary` style
- Add inline SVG mail icon
- Add hint about in-app feedback
- Add "Back to generator" link

### 3.3 Contact Component Replacement — React SPA

In `frontend/src/legacy-app.jsx`, replace the `Contact` component with an email-only version:
- Remove all form state (useState for values, errors, sent, submit)
- Remove useToast usage for Contact (keep for other components)
- Add `<Button variant="primary" iconLeft="mail">` with `mailto:` onClick

### 3.4 verify-build.mjs Rewrite

Split validation into two lists:
- `adsenseRequired`: `['dist/index.html']` — must have AdSense
- `adsenseForbidden`: `['dist/pages/about.html', 'dist/pages/contact.html', 'dist/pages/privacy.html', 'dist/pages/terms.html']` — must NOT have AdSense

### 3.5 Sprint 1 Build Verification

```bash
cd dnd-prompt-forge/frontend
npm run build
node scripts/verify-build.mjs
```

---

## 4. Sprint 2: 5 Content Guide Pages + Routing/Navigation/Sitemap

### 4.1 Guide Page URL Mapping

| Slug | Clean URL | File |
|------|-----------|------|
| character-portrait-guide | `/character-portrait-guide` | `pages/character-portrait-guide.html` |
| token-guide | `/token-guide` | `pages/token-guide.html` |
| monster-guide | `/monster-guide` | `pages/monster-guide.html` |
| npc-guide | `/npc-guide` | `pages/npc-guide.html` |
| scene-guide | `/scene-guide` | `pages/scene-guide.html` |

### 4.2 Nginx Routing Specification

Add 15 new `location` blocks (5 clean URL + 5 trailing slash 301 + 5 /pages/*.html 301).

### 4.3 Sitemap Expansion

Expand from 6 to 11 URLs, adding 5 guide page entries with priority 0.8.

### 4.4 Guide Page HTML Template

Each guide page includes:
- AdSense script in `<head>` (these are content pages)
- `<link rel="canonical">` to clean URL
- `og:type` = `article`, JSON-LD `@type` = `Article`
- 7 mandatory content sections
- CTA block linking to generator
- Related guides links
- Minimal text footer

### 4.5 Homepage Guide Card Navigation

New `GuideCards` component in `legacy-app.jsx`, inserted after `<FAQ />`.

### 4.6 Footer Navigation — Guides Section

New `FOOTER_GUIDES` array and column in Footer component.

### 4.7 verify-build.mjs Update

Add 5 guide pages to `adsenseRequired` list after Sprint 2.

### 4.8 copy-static.mjs — No Change Needed

Already copies `pages/` directory recursively.

---

## 5. Security & Performance

- **No new dependencies**: All changes use existing CSS classes, existing React primitives, and existing Nginx routing patterns.
- **No sensitive data changes**: Contact email is public.
- **Cache invalidation**: Cloudflare cache purge required after deployment.
- **Nginx config validation**: Must run `nginx -t` before deployment.

---

## 6. Developer Pre-flight Checklist

- [ ] Sprint 1: Remove AdSense from exactly 4 files (about, contact, privacy, terms). Do NOT touch `index.html`.
- [ ] Sprint 1: Replace Contact form in BOTH static HTML and React component.
- [ ] Sprint 1: Rewrite `verify-build.mjs` BEFORE running build.
- [ ] Sprint 2: Each guide page MUST have AdSense script in `<head>`.
- [ ] Sprint 2: Each guide page MUST have canonical, og:type=article, Article JSON-LD.
- [ ] Sprint 2: Nginx location blocks use `=` exact match.
- [ ] Sprint 2: Guide page links in Footer use `href` (full page load), not `onClick`.
- [ ] Sprint 2: `copy-static.mjs` does NOT need modification.
- [ ] Sprint 2: After creating guide pages, update `verify-build.mjs` adsenseRequired list.
- [ ] Both: Run `nginx -t` + full build + verify-build.mjs before committing.
- [ ] Both: Privacy policy update is DEFERRED (not in this Sprint).
