# dnd.whatai.me Search Ranking Recovery Plan

## Current conclusion

The message "No keywords are driving traffic" is consistent with the current
site state. It does not prove that backlinks are the only missing factor.

Observed on June 8, 2026:

- The public sitemap contains only one URL: `https://dnd.whatai.me/`.
- The public `robots.txt` is modified by Cloudflare Managed robots.txt.
- The public `robots.txt` still references the old sitemap domain
  `https://dndpromptforge.com/sitemap.xml`.
- The site recently received a Google Safe Browsing deceptive-pages warning.
- The repository currently has one main tool page and four legal/information
  HTML files, but only the homepage is listed in the public sitemap.

With one discoverable page and unresolved trust/crawl signals, there are too few
search intents for ranking tools to detect.

## Priority 0: clear security and crawl blockers

1. In Google Search Console, confirm that the Security Issues report is clear.
2. If an issue remains, finish remediation and request a security review.
3. Disable Cloudflare Managed robots.txt:
   - Cloudflare dashboard
   - Security Settings or Security > Bots
   - Disable "Instruct AI bot traffic with robots.txt"
4. Deploy the latest frontend image without cache.
5. Clear the host Nginx proxy cache and Cloudflare cache.
6. Verify that the public file contains only:

```text
User-agent: *
Allow: /

Sitemap: https://dnd.whatai.me/sitemap.xml
```

7. In Search Console URL Inspection, test the live homepage and request
   indexing once the security report is clear.

## Priority 1: establish a valid indexable baseline

The sitemap should contain every real, canonical, HTTP 200 page and no fake or
fallback routes.

Initial sitemap:

- `https://dnd.whatai.me/`
- `https://dnd.whatai.me/about`
- `https://dnd.whatai.me/privacy`
- `https://dnd.whatai.me/terms`
- `https://dnd.whatai.me/contact`

Before submitting these URLs, ensure each path returns its own HTML content and
canonical URL rather than the homepage SPA fallback.

Search Console checks:

- Page indexing report
- URL Inspection live test
- Crawled page HTML
- User-declared canonical
- Google-selected canonical
- Sitemap processing status

## Priority 2: publish useful search landing pages

Do not restore the old long-tail links until each URL has a real static page.
Start with five pages based on existing product workflows:

1. `/dnd-character-prompt-generator`
2. `/dnd-token-prompt-generator`
3. `/dnd-monster-prompt-generator`
4. `/dnd-npc-prompt-generator`
5. `/dnd-scene-prompt-generator`

Each page should include:

- A unique title and meta description.
- One clear H1 matching the page intent.
- Original explanatory content written for users.
- A working, prefilled entry point into the generator.
- At least one complete prompt example.
- Relevant FAQ content.
- Self-referencing canonical URL.
- Links to the homepage and related generator pages.
- Inclusion in the sitemap only after deployment returns HTTP 200.

Avoid mass-producing near-duplicate race/class combinations. Expand only after
Search Console shows impressions for the core five pages.

## Priority 3: build discovery and authority

Only begin active link building after the site is clean and indexed.

Good initial sources:

- Relevant DND tool directories.
- Virtual tabletop resource lists.
- Dungeon-master community resource pages.
- GitHub README and project releases.
- Original tutorials demonstrating prompt workflows.
- Shareable example collections that provide value without requiring signup.

Avoid purchased links, automated directory submissions, comment spam, and
large-scale reciprocal link exchanges.

## Measurement

Review weekly in Search Console:

- Valid indexed pages.
- Pages discovered but not indexed.
- Impressions by query.
- Click-through rate by page.
- Google-selected canonical.
- Security and manual-action status.

Initial success criteria:

- Security Issues report is clear.
- Public robots.txt uses the live domain and standard directives.
- Sitemap is accepted without errors.
- Homepage and five core landing pages are indexed.
- Search Console records non-branded impressions for at least three pages.

## Expected timing

After security clearance and sitemap submission, recrawling may take several
days to several weeks. Keyword tools can lag behind Search Console, so Search
Console impressions should be treated as the primary early signal.
