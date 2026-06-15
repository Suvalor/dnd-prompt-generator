# DND Core Guide Content and Layout Review

Date: 2026-06-15

## Resolution status

Resolved on 2026-06-15. The site now contains six independent core guides, publishes the shared static stylesheet, passes responsive layout checks, and uses revised model guidance that avoids unsupported absolute claims.

## Findings

### Resolved: Six core guides are implemented

The final set contains:

1. Character portrait prompts
2. VTT token prompts
3. Monster and creature prompts
4. NPC portrait prompts
5. Fantasy scene prompts
6. Full-body character prompts

The Full Body guide is connected through the homepage, footer, Sitemap, Nginx clean URL, build verification, acceptance tests, and related-guide links.

### Resolved: Static styles are published in the production build

The static copy step now publishes `css/style.css`. Build verification requires the file and checks every guide's stylesheet reference. Desktop and 390px-wide browser checks show the intended typography, 720px prose width, wrapped prompt examples, and no horizontal overflow.

### Resolved: Guide claims were made conditional

The five guides contain useful, differentiated advice, examples, failure modes, templates, and FAQs. Each is approximately 1,800 to 2,100 words. However, several model-specific statements are presented as universal facts when behavior varies by model version, settings, and image-generation provider.

Revised examples include:

- “Avoid rim light or backlit” should explain the trade-off rather than prohibit those techniques.
- “DALL-E 3 is the best model for VTT tokens” and “the best model for NPCs” should be framed as a workflow preference, not a measured ranking.
- “The model prioritizes the beginning most heavily” is not consistently true across providers.
- “AI image models cannot produce accurate top-down battle maps” and dedicated tools “will always outperform” them are overbroad.
- Version-specific Midjourney and DALL-E guidance should be dated or periodically reviewed.

The character portrait FAQ typo was also corrected.

### Resolved: Tests cover the missing release requirements

The 67 acceptance checks pass because they confirm file presence, headings, metadata, links, and AdSense placement. They do not detect:

- the missing sixth guide;
- broken stylesheet references;
- horizontal overflow;
- duplicated or low-quality guide content;
- unsupported factual claims;
- navigation to every clean production URL.

The suite now requires all six pages, the sixth navigation entry, 12 Sitemap URLs, and the published shared stylesheet. Responsive overflow was additionally verified in a production browser preview.

### Resolved: The inline SVG CSS warning was removed

The inline SVG is now URL-encoded correctly, and the CSS minifier no longer reports the syntax warning.

## Privacy revision completed

Both Privacy sources were updated to match the implementation:

- exact update date;
- server and local fallback behavior;
- anonymous 10-day session cookie;
- browser fingerprint, IP, quota, and audit processing;
- optional persisted feedback;
- no unsupported analytics claim;
- Google AdSense cookie and partner-site disclosure;
- cookie and advertising choices;
- sensitive-information warning and direct privacy contact.

## Verification

- `npm run build`: passed.
- Business acceptance tests: 77 passed, 0 failed.
- Six guide pages: 1,630 to 2,083 words each, with 8 or 9 major sections.
- Production preview: desktop and 390px mobile layouts have no horizontal overflow.
- Privacy content and shared static styling are present.
