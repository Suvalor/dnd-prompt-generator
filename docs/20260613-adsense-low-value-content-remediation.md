# AdSense Low-Value Content Remediation

## Conclusion

The rejection is consistent with the current site implementation. Two separate
issues are present:

1. Google advertising code is loaded on screens that are primarily legal,
   navigational, or behavioral rather than publisher-content pages.
2. The site currently presents too little reliably indexable, original,
   topic-specific content to demonstrate sustained publisher value.

The strongest implementation-level issue is that the build explicitly requires
the AdSense script on About, Contact, Privacy, and Terms pages. With Auto ads
enabled, Google may place ads on those screens even though they are not the
main content users visit the site to consume.

This document is a diagnosis and remediation scope. It does not claim that
Google guarantees approval after these changes.

## Verification method

Checked on June 13, 2026:

- Google Publisher Policies and AdSense content-quality guidance.
- Repository HTML, React routes, content sections, build verification, sitemap,
  and advertising code placement.
- Live `dnd.whatai.me` responses, AdSense script presence, `ads.txt`, titles,
  and canonical tags.

Live `ads.txt` is valid:

```text
google.com, pub-9123849728110588, DIRECT, f08c47fec0942fa0
```

Therefore, this rejection is not caused by a missing `ads.txt`.

## Policy interpretation

Google does not allow ads on screens that:

- Have no publisher content or low-value content.
- Are under construction.
- Exist mainly for alerts, navigation, or other user actions.

Google also expects enough unique content to establish the site's subject,
provide real user value, attract repeat visits, and support clear navigation.

There is no official universal minimum article count or word count. The
decision is based on the actual usefulness and originality of the site.

## Confirmed site risks

### 1. AdSense code is forced onto non-content screens

The following files load the AdSense script:

- Homepage
- About
- Contact
- Privacy
- Terms

`frontend/scripts/verify-build.mjs` fails the build if the script is absent from
any of those five pages. This turns legal and action-oriented pages into
advertising inventory by design.

High-risk screens:

- Contact form
- Contact success/thank-you state
- Privacy policy
- Terms of use
- 404 state
- Empty/loading/error generator states
- Navigation-only or redirect/fallback pages

The Contact screen is particularly risky because its primary purpose is a user
action, not consuming publisher content.

### 2. Contact functionality appears unfinished

The static Contact page contains a form without a real submission destination.
The React Contact screen changes to a success message without sending the
message to a backend.

This creates an under-construction or misleading user experience and should be
fixed independently of AdSense.

### 3. Too few independent publisher-content pages

The homepage contains useful interface guidance, examples, limitations, and
FAQs, but most value remains concentrated on one tool page.

The additional public pages are primarily:

- About
- Privacy
- Terms
- Contact
- Excel utility

Legal and contact pages do not establish editorial depth. The Excel converter
is a separate utility with almost no explanatory publisher content.

### 4. Search and canonical defects reduce visible content value

The existing indexing diagnosis confirmed:

- The sitemap only lists the homepage.
- Clean routes such as `/about` currently serve homepage HTML.
- Static content exists at `/pages/*.html`.
- Canonical destinations and actual content do not match.
- Multiple URL variants return 200.

An AdSense reviewer may therefore see one canonical page, duplicate fallback
pages, and several thin utility/legal screens instead of a coherent content
site.

### 5. Auto ads are poorly matched to a tool-first SPA

The homepage mixes:

- Form controls.
- Loading and output states.
- Copy actions.
- Navigation and legal routes.
- Publisher-written guides and examples.

Auto ads cannot reliably understand which application state is safe to
monetize. A route change in the SPA also does not unload the AdSense script, so
ads loaded on the homepage can remain relevant to later legal/action screens.

## Immediate remediation

### Priority 0: stop creating prohibited inventory

Before requesting another review:

1. Remove AdSense code from About, Contact, Privacy, and Terms.
2. Remove the build rule requiring AdSense on those pages.
3. Do not show ads on 404, form-success, empty, loading, error, or redirect
   states.
4. Do not place ads inside or immediately adjacent to generator controls,
   generated output, copy buttons, or navigation.
5. Pause Auto ads while restructuring the site.

The safest review configuration is:

- Keep the AdSense site-verification code only where required.
- Disable Auto ads.
- Add manual ad units later, only to approved content-rich pages and sections.

If Auto ads must remain enabled, configure URL exclusions and ensure legal
routes are real page loads without the advertising script. The current SPA
fallback makes URL exclusions less reliable.

### Priority 1: fix incomplete user experiences

Contact must either:

- Submit to a real backend or form provider and accurately report success; or
- Be replaced with a real email/contact method.

Do not display advertising on the Contact or thank-you screen.

### Priority 2: fix URL and indexing architecture

Complete the work defined in:

```text
docs/20260612-google-indexing-diagnosis.md
```

Required outcome:

- One canonical URL per page.
- Clean URLs serve their own content.
- Old URL variants redirect with 301.
- HTTP redirects to HTTPS.
- Sitemap lists all canonical content pages.
- Excel converter receives a canonical URL.

Do not request AdSense review while Google still sees canonical conflicts and
homepage fallback duplicates.

## Content development requirement

The site needs original pages that help users accomplish specific DND prompt
tasks without requiring them to use the generator first.

Recommended first content set:

1. DND character portrait prompt guide.
2. Top-down VTT token prompt guide.
3. DND monster prompt guide.
4. NPC portrait and role prompt guide.
5. Fantasy scene and encounter prompt guide.

Each page should contain genuinely distinct material:

- When the prompt type is useful.
- Composition decisions and trade-offs.
- Complete before/after examples.
- Common failure patterns and corrections.
- Model-specific guidance.
- A manually reviewed prompt template.
- Relevant FAQs.
- Links to related guides and the generator.

Avoid:

- Producing many race/class pages from the same template.
- Repeating homepage text with different keywords.
- Publishing raw automatically generated prompts without human review.
- Treating Privacy, Terms, Contact, tags, or search results as content pages.

The goal is not an arbitrary word count. A page should solve a specific problem
well enough that users would reasonably bookmark, share, or revisit it.

## Excel converter treatment

The Excel ratio converter should not be monetized in its current form. It is
primarily an action-oriented utility screen.

It can remain available as an extra tool, but before ads are considered it
would need meaningful publisher content such as:

- What problem the converter solves.
- Supported Excel paste formats.
- Worked allocation examples.
- Rounding behavior.
- Formula and precision limitations.
- Privacy explanation.
- Troubleshooting guidance.

Even after adding this material, ads should remain separated from the input,
formula controls, output table, and copy button.

## Recommended advertising architecture

### Pages with no ads

- Contact
- Privacy
- Terms
- About
- 404
- Thank-you/success pages
- Tool empty/loading/error states
- Excel converter for the current review

### Candidate pages for future manual ads

- Original long-form DND guides.
- Content-rich tutorials with complete examples.
- Homepage guide sections, only if ads are clearly separated from tool
  controls and generated output.

Start with fewer manual placements. Do not let advertising occupy more visual
attention than the publisher content.

## Privacy follow-up

The privacy policy currently mentions advertising in general terms. Before
serving ads, confirm that it accurately discloses:

- Google's and third parties' use of cookies or similar identifiers.
- Advertising data collection and use.
- A visible link to Google's explanation of how partner-site data is used.
- Consent requirements applicable to EEA, UK, and Swiss users.

This is not the reported rejection reason, but it should be corrected before
production monetization.

## Re-review checklist

Do not apply for review until all items are true:

- [ ] Auto ads are disabled during remediation.
- [ ] Legal, contact, action, empty, error, and success screens contain no ads.
- [ ] Contact submission is real or replaced with an honest contact method.
- [ ] Canonical and routing defects are fixed.
- [ ] Sitemap includes every canonical content page.
- [ ] Several original, useful, independently indexable DND guides are live.
- [ ] Internal navigation exposes those guides.
- [ ] No generated doorway or near-duplicate pages are present.
- [ ] Mobile and desktop navigation work.
- [ ] Privacy disclosures match the actual advertising setup.
- [ ] Search Console live tests show the intended content and canonical.
- [ ] The site has been crawled again after deployment.

## Suggested sequence

1. Disable Auto ads and remove scripts from non-content pages.
2. Fix Contact functionality.
3. Fix routing, canonicals, redirects, and sitemap.
4. Publish and internally link the first substantive guide pages.
5. Verify rendering and indexing in Search Console.
6. Wait for recrawl and inspect the live site as a new visitor.
7. Request AdSense review.
8. After approval, introduce manual ads conservatively.

## Confidence boundary

High confidence:

- Advertising code is intentionally loaded on legal/contact pages.
- Contact is not a real submission flow.
- Sitemap and canonical architecture currently weaken the site's content
  signals.
- The site lacks multiple substantial independently indexable content pages.

Medium confidence:

- Auto ads actually rendered on every flagged screen during Google's review.
  The script is present, but the exact review-time placement is unavailable.

Unknown:

- The exact URL or screenshot used by the AdSense reviewer.
- Whether Google evaluated a cached version from before the latest deployment.
- Whether any additional account-level policy issue exists.

## AutoDev 执行进度

- [x] Phase 1：需求对齐 / PRD（L2，用户已确认 Contact 邮箱 + Privacy 方案 + Auto ads 状态）
- [x] Phase 1.5：价值审查
- [x] Phase 2：设计与架构
- [x] Phase 3：实现
- [x] Phase 4：代码审查
- [x] Phase 5：业务验收

### 最新状态
- 当前阶段：已完成
- 最近更新时间：2026-06-14
- 变更文件：pages/about.html, pages/contact.html, pages/privacy.html, pages/terms.html, pages/character-portrait-guide.html, pages/token-guide.html, pages/monster-guide.html, pages/npc-guide.html, pages/scene-guide.html, src/legacy-app.jsx, js/prose-pages.jsx, js/content-sections.jsx, js/app.jsx, js/footer.jsx, scripts/verify-build.mjs, deploy/nginx.conf, sitemap.xml, css/style.css
- 验证命令：npm run build + verify-build.mjs + grep 结构断言 + Docker curl 测试
- 验证结果：67/67 断言通过，22/22 验收标准通过
- 阻塞项：无
- 假设与取舍：隐私政策更新延后到 AdSense 上线前；Auto ads 暂停需用户在 Dashboard 操作；skip-link/main landmark 为技术债
