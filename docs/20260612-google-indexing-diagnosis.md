# Google Indexing Diagnosis for dnd.whatai.me

## Executive conclusion

The indexing exclusions shown in Google Search Console come from multiple
independent causes. The primary confirmed defect is a mismatch between public
URLs, Nginx fallback routing, and canonical tags.

Live checks performed on June 12, 2026 found:

- Public pages currently return HTTP 200 to both a normal user agent and
  Googlebot.
- `/about`, `/privacy`, `/contact`, and similar clean URLs serve the homepage
  HTML because Nginx falls back to `/index.html`.
- The actual static content exists at `/pages/about.html`,
  `/pages/privacy.html`, and similar URLs.
- Those static files declare the clean URLs as canonical, even though the clean
  URLs do not serve the same content.
- The live sitemap contains only the homepage.
- HTTP does not redirect to HTTPS.
- `/index.html`, trailing-slash variants, clean routes, and `/pages/*.html`
  variants can all return HTTP 200.
- The Excel ratio converter has no canonical tag and is absent from the
  sitemap.

This combination explains the canonical and duplicate-page exclusions. The 403
exclusion was not reproducible during the live check and is likely historical
or intermittent at the Cloudflare/WAF layer.

## Confirmed evidence

### 1. Clean URLs return homepage content

Live response for `https://dnd.whatai.me/about`:

- Status: 200
- Title: `DND Character Prompt Generator | Free AI Image Prompts`
- Canonical: `https://dnd.whatai.me/`

Live response for `https://dnd.whatai.me/pages/about.html`:

- Status: 200
- Title: `About DND Prompt Forge | Free DND Character Prompt Generator`
- Canonical: `https://dnd.whatai.me/about`

The declared canonical destination therefore serves different content. The same
pattern occurs for privacy and contact pages.

The repository cause is the SPA fallback in `deploy/nginx.conf`:

```nginx
location / {
    try_files $uri $uri/ /index.html;
}
```

There are no exact routes mapping `/about` to `/pages/about.html`.

### 2. Sitemap only contains the homepage

The live and repository sitemap currently contains only:

```text
https://dnd.whatai.me/
```

The About, Privacy, Terms, Contact, and Excel converter pages are not submitted
through the sitemap.

### 3. Duplicate URL variants return 200

The following variants currently return 200 without canonical redirects:

- `http://dnd.whatai.me/`
- `https://dnd.whatai.me/`
- `https://dnd.whatai.me/index.html`
- `https://dnd.whatai.me/about`
- `https://dnd.whatai.me/about/`
- `https://dnd.whatai.me/pages/about.html`
- Query-string variants of static pages

This leaves Google to choose among multiple competing URLs.

### 4. Current 403 is not reproducible

On June 12, 2026, all checked URLs returned 200 to both normal and Googlebot
user agents:

- Homepage
- About
- Privacy
- Terms
- Contact
- Excel ratio converter
- robots.txt
- sitemap.xml

The Search Console 403 row may therefore represent:

- A historical crawl before a Cloudflare rule was changed.
- An intermittent Cloudflare Bot/WAF challenge.
- A specific URL not included in the current test.
- Rate limiting, IP reputation, or geographic filtering.

The exact affected URL and Google crawl timestamp are required to identify the
specific Cloudflare event.

## Mapping to Search Console reasons

### Alternate page with proper canonical tag

Likely applies to `/pages/*.html` pages that point to clean canonical URLs.
Alternate-page classification is normally acceptable, but not when the
canonical destination serves unrelated homepage content.

### Blocked due to access forbidden (403)

Not currently reproducible. Treat this as a Cloudflare/WAF investigation rather
than a frontend metadata issue until the exact URL is known.

### Crawled - currently not indexed

Contributing factors:

- Only the homepage is present in the sitemap.
- Several public URLs resolve to duplicate homepage content.
- The Excel tool lacks a canonical tag.
- Google receives weak and conflicting URL ownership signals.

### Duplicate, Google chose different canonical than user

Directly explained by the clean-route fallback and multiple 200 URL variants.
Google cannot reliably select the declared canonical when that URL serves
different content.

## Recommended repair

### Priority 0: establish one URL per page

Use clean canonical URLs:

- `/`
- `/about`
- `/privacy`
- `/terms`
- `/contact`
- `/excel-ratio-converter`

Configure Nginx so each clean URL serves its actual static HTML rather than the
homepage fallback.

Redirect old static URLs with HTTP 301:

- `/pages/about.html` -> `/about`
- `/pages/privacy.html` -> `/privacy`
- `/pages/terms.html` -> `/terms`
- `/pages/contact.html` -> `/contact`
- `/pages/excel-ratio-converter.html` -> `/excel-ratio-converter`

Also redirect:

- HTTP -> HTTPS
- `/index.html` -> `/`
- Trailing-slash variants to the selected canonical form

### Priority 1: correct metadata

- Keep self-referencing canonicals on every indexable page.
- Add a canonical to the Excel converter.
- Make Open Graph URLs match canonical URLs.
- Ensure every canonical destination returns its own HTTP 200 HTML.
- Do not canonicalize distinct content to the homepage.

### Priority 2: rebuild sitemap

Include every canonical, indexable page:

```text
https://dnd.whatai.me/
https://dnd.whatai.me/about
https://dnd.whatai.me/privacy
https://dnd.whatai.me/terms
https://dnd.whatai.me/contact
https://dnd.whatai.me/excel-ratio-converter
```

Do not include redirected `/pages/*.html` URLs.

### Priority 3: investigate the 403 event

In Search Console:

1. Open the 403 issue and record the exact affected URL.
2. Run URL Inspection and test the live URL.
3. Record the last crawl timestamp and crawled-as user agent.

In Cloudflare:

1. Search Security Events using the affected URL and crawl timestamp.
2. Check WAF custom rules, Bot Fight Mode, rate limiting, Browser Integrity
   Check, country restrictions, and managed challenges.
3. Confirm verified search-engine bots are not challenged.
4. Public GET/HEAD requests for HTML, robots.txt, and sitemap.xml should not
   depend on cookies or JavaScript challenges.

## Validation checklist

After implementation:

1. Every canonical URL returns HTTP 200 and unique page content.
2. Every noncanonical variant returns one HTTP 301 to its canonical URL.
3. HTTP redirects to HTTPS.
4. Canonical tags exactly match final URLs.
5. Sitemap contains only canonical HTTP 200 URLs.
6. Googlebot receives the same status, title, canonical, and content as a
   normal browser.
7. Search Console live tests pass before selecting "Validate fix."

## Expected Search Console behavior

Canonical and duplicate classifications will not disappear immediately.
After deployment and validation, Google must recrawl the affected URLs. Status
changes may take several days to several weeks.

## AutoDev 执行进度

- [x] Phase 1：需求对齐 / PRD（L1 跳过独立 PRD）
- [x] Phase 2：架构技术契约
- [x] Phase 3：实现
- [x] Phase 4：代码审查
- [x] Phase 5：业务验收（L1 跳过独立业务验收）

### 最新状态
- 当前阶段：已完成
- 最近更新时间：2026-06-12
- 变更文件：deploy/nginx.conf, frontend/pages/excel-ratio-converter.html, frontend/sitemap.xml, frontend/pages/privacy.html, docker-compose.yml
- 验证命令：curl 测试 12 项验收矩阵（本地 Docker 验证）
- 验证结果：12/12 通过
- 阻塞项：无
- 假设与取舍：HTTP→HTTPS 重定向由 Cloudflare "Always Use HTTPS" 处理；P3 403 调查需用户在 Search Console/Cloudflare 操作
