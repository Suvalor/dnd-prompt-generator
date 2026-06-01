# DND Prompt Generator UI Outline

Date: 2026-06-01
Status: UI outline before implementation
Source docs:

- `PLAN.md`
- `docs/scope-change/20260601-dnd-prompt-generator-prd.md`
- `docs/scope-change/20260601-dnd-prompt-generator-dev-doc.md`
- `docs/scope-change/20260601-dnd-prompt-generator-seo-plan.md`

## 1. Design Goal

Build a free, SEO-ready DND prompt tool where the generator is the main product, not a buried conversion widget.

The first screen should immediately answer the search intent:

```text
I need a copy-ready DND character, token, NPC, monster, or scene prompt for an AI image tool.
```

Primary UI outcome:

- User understands the tool in 3 seconds.
- User can start generating above the fold.
- User can copy useful output without login.
- Google can crawl meaningful content, headings, examples, FAQ, and internal links.

## 2. Product Tone

Recommended direction: practical fantasy workshop.

The UI should feel like a sharp tabletop utility made for DMs and players, not a mystical landing page. It can use fantasy texture and atmosphere, but the working surface should stay readable, compact, and fast.

Avoid:

- A marketing-only hero before the tool.
- Overly dark low-contrast fantasy art that hurts form readability.
- Purple-blue AI SaaS gradients.
- Decorative cards inside cards.
- Vague copy such as "unlock your imagination" without immediate utility.

Use:

- A parchment/light workbench base with dark ink text.
- Strong accent colors from tabletop materials: brass, crimson wax, emerald glass, charcoal ink.
- Small DND-flavored details: dice marks, stat-block dividers, map-grid lines, compact badges.
- Dense but calm tool layout, closer to a character-sheet workbench than a brand campaign.

## 3. Page Architecture

Homepage route: `/`

Recommended section order:

1. Header
2. First viewport generator
3. Output panel
4. Example prompt gallery
5. Prompt type guide
6. How it works
7. Limitations and model compatibility
8. FAQ
9. Internal links
10. Footer

The generator and its empty output state should be visible in the first viewport on desktop. On mobile, the form appears first and the output follows immediately after the primary action.

## 4. Header

Purpose: lightweight orientation and crawlable navigation.

Content:

- Logo/name: `DND Prompt Forge`
- Primary nav links:
  - Character Prompt
  - Token Prompt
  - Monster Prompt
  - Scene Prompt
  - About
  - Contact

Layout:

- Desktop: compact horizontal header, sticky optional.
- Mobile: logo left, menu button right, expanded sheet with crawlable anchor links if implemented.

Notes:

- Keep header height modest so the tool remains above the fold.
- Do not use the logo as the only brand signal; the H1 still carries the SEO term.

## 5. First Viewport

### Left/Top Content

H1:

```text
DND Character Prompt Generator
```

First paragraph:

```text
Use this DND Character Prompt Generator to turn your race, class, style, weapon, and backstory idea into a copy-ready AI image prompt for portraits, VTT tokens, NPCs, monsters, and fantasy scenes.
```

Support line:

```text
Free, no login required. Copy prompts into Midjourney, ChatGPT, Gemini, Leonardo, Stable Diffusion, or any image model.
```

Trust/utility badges:

- No login
- Prompt only
- Works with any image tool
- Includes negative prompt

### Tool Placement

The generator should be the dominant object in the first viewport.

Desktop layout:

- Two-column workbench.
- Left column: form.
- Right column: output panel or example empty state.

Mobile layout:

- Single column.
- H1 and one paragraph.
- Form.
- Generate button.
- Output panel.

## 6. Generator Form

### Primary Structure

Use a stepped visual hierarchy without forcing a multi-step wizard:

1. Prompt type
2. Core DND details
3. Visual direction
4. Optional refinements
5. Target model

This keeps the form scannable while allowing fast completion.

### Fields

Prompt type:

- Segmented control with icons or compact labels:
  - Portrait
  - Full body
  - Token
  - NPC
  - Monster
  - Scene

Core fields:

- Race / creature type
- Class / role
- Short description

Visual direction:

- Visual style
- Mood
- Background setting

Optional refinements:

- Gender presentation
- Age
- Alignment
- Armor
- Weapon
- Magic/spell theme
- Color palette
- Camera angle

Target model:

- Midjourney
- ChatGPT
- Gemini
- Leonardo
- Stable Diffusion
- General purpose

### Field UX

- Use examples as placeholders, not long instructional paragraphs.
- Place optional fields in a collapsible `More details` area.
- Keep required fields visually obvious.
- Provide smart defaults for style, mood, and target model.
- Show token-specific hints when `Token` is selected.

Primary action:

```text
Generate Prompt
```

Secondary actions:

- Clear
- Load example

## 7. Output Panel

### Empty State

Show an example result preview instead of a blank box.

Empty state content:

- Example title: `Tiefling Warlock Portrait`
- Short sample prompt excerpt.
- Note: `Fill the form to generate your own copy-ready prompt.`

### Loading State

Use a compact progress state:

- Button disabled with `Generating...`
- Output panel shows 3 skeleton blocks:
  - Main prompt
  - Short prompt
  - Negative prompt

Avoid theatrical loading copy. Keep it fast and utilitarian.

### Success State

Output blocks:

1. Main prompt
2. Short prompt
3. Negative prompt
4. Style notes
5. Usage tip
6. Token notes when output type is token

Each text block should have:

- Title
- Copy button
- Monospaced or prompt-friendly body styling
- Small metadata row if available:
  - target model
  - template version
  - memory rule version

Actions:

- Copy main prompt
- Copy short prompt
- Copy negative prompt
- Regenerate
- Mark useful
- Mark not useful

### Feedback State

After `Not useful`, reveal reason chips:

- Too generic
- Not DND-specific enough
- Wrong style
- Missing details
- Too long
- Too short
- Other

Optional comment textarea:

```text
What should future prompts do differently?
```

Feedback confirmation:

```text
Thanks. Future prompts will use this feedback.
```

## 8. Example Prompt Gallery

Purpose:

- Supports SEO depth.
- Helps users understand output quality.
- Provides empty-state content and internal examples.

Recommended examples:

- Tiefling Warlock portrait prompt
- Elf Ranger full-body prompt
- Dragonborn Paladin token prompt
- Goblin merchant NPC prompt
- Haunted tavern scene prompt

Each example card:

- Output type badge
- Race/class or scene name
- Short prompt excerpt
- `Use this example` action
- Link to a related long-tail page when available

Keep cards as individual repeated items only. Do not wrap the gallery in another decorative card.

## 9. Prompt Type Guide

Purpose: clarify why output type matters.

Suggested H2:

```text
Generate Portraits, Tokens, NPCs, Monsters, And Scenes
```

Layout:

- Responsive 2 or 3 column grid.
- One item per prompt type.
- Each item explains the composition difference:
  - Portrait: face, costume, lighting, personality.
  - Full body: silhouette, armor, pose, weapon.
  - Token: top-down view, centered figure, readable outline.
  - NPC: role, attitude, memorable traits.
  - Monster: anatomy, threat, scale, environment.
  - Scene: place, mood, lighting, encounter hook.

## 10. How It Works

Suggested H2:

```text
How The DND Prompt Generator Works
```

Three steps:

1. Choose the prompt type.
2. Add DND details.
3. Copy the prompt into your image tool.

Include a fourth small note about feedback:

```text
If a result is not useful, your feedback helps adjust future prompt rules.
```

## 11. Limitations And Compatibility

This section should be visible enough for user trust and AdSense safety.

Content points:

- The tool generates prompts, not final images.
- Output quality depends on the third-party image model.
- It does not require login for MVP.
- Avoid using copyrighted character names or official art claims.
- DND is a trademark of its respective owner; the site should not imply official affiliation.

## 12. FAQ

Suggested H2:

```text
DND Prompt Generator FAQ
```

FAQ items:

- What is a DND character prompt generator?
- Does this tool generate images?
- Can I use these prompts in Midjourney or ChatGPT?
- Can it create top-down VTT token prompts?
- Is the DND prompt generator free?
- Do I need to log in?

Implementation note:

- Add FAQ JSON-LD only when the same FAQ is visible on the page.

## 13. Internal Links

Footer and content links should expose crawlable routes:

- `/dnd-character-prompt-generator`
- `/dnd-token-prompt-generator`
- `/dnd-monster-prompt-generator`
- `/dnd-npc-prompt-generator`
- `/dnd-scene-prompt-generator`
- `/fantasy-character-prompt-generator`
- `/tiefling-warlock-prompt-generator`
- `/elf-ranger-prompt-generator`
- `/dragonborn-paladin-token-prompt`
- `/dnd-tavern-scene-prompt`

Avoid linking to pages that do not exist after launch unless they are deliberately excluded from the sitemap.

## 14. Visual System

### Layout

- Max content width: about 1120-1200px.
- First viewport: dense two-column workbench on desktop.
- Section bands: full-width, not floating card stacks.
- Repeated examples may use cards with radius 8px or less.

### Typography

Suggested pairing:

- Display: a readable fantasy/editorial serif for H1/H2.
- Body: a high-legibility humanist sans or bookish serif.
- Prompt output: monospace or code-friendly font.

Avoid tiny fantasy fonts in form controls.

### Color

Suggested palette:

- Base: warm parchment / off-white.
- Text: charcoal ink.
- Surface: clean vellum or light stone.
- Accent 1: brass/gold for primary actions.
- Accent 2: crimson wax for warnings/negative feedback.
- Accent 3: emerald or deep teal for success/useful state.

Keep contrast strong and do not let the interface become a one-color brown parchment theme.

### Iconography

Use icons only where they reduce reading:

- Copy
- Refresh/regenerate
- Check/useful
- Alert/error
- Menu
- Prompt type icons where available

Use tooltips for unfamiliar icons.

## 15. Responsive Behavior

Desktop:

- Header + first viewport should fit without hiding the tool.
- Form and output panel sit side by side.
- Optional fields may use two-column rows.

Tablet:

- Tool remains two columns if width allows.
- Otherwise stack form above output.

Mobile:

- Single-column.
- Prompt type segmented control wraps cleanly.
- Copy buttons remain tappable.
- Optional fields collapse by default.
- No text should overflow buttons or chips.

## 16. Accessibility And Usability

Minimum requirements:

- Real labels for all inputs.
- Keyboard-accessible controls.
- Visible focus states.
- Error messages linked to fields where practical.
- Copy action confirms success.
- Loading state announces progress.
- Color is never the only indicator for feedback.
- Form should remain usable at 320px width.

## 17. SEO Implementation Notes

Homepage must include:

- Title: `DND Character Prompt Generator | Free AI Image Prompts`
- Meta description from SEO plan.
- H1: `DND Character Prompt Generator`
- Natural first paragraph with the primary keyword.
- Semantic H2 structure.
- Crawlable examples and FAQ.
- Canonical URL.
- OG/Twitter metadata.
- SoftwareApplication JSON-LD.
- FAQPage JSON-LD only if FAQ is visible.

Avoid:

- `meta keywords`
- Keyword stuffing
- Important content rendered only after user interaction

## 18. MVP Screen Inventory

Required screens/states before launch:

- Homepage default empty state.
- Homepage loading state.
- Homepage success state.
- Homepage API error state.
- Feedback submitted state.
- About page.
- Privacy page.
- Terms page.
- Contact page.
- 404 page.

Recommended next after MVP:

- Core landing page template for token, monster, NPC, and scene routes.
- Long-tail route template with prefilled examples.
- Search Console iteration dashboard or checklist.

## 19. Acceptance Checklist

- [ ] Generator appears in the first viewport.
- [ ] H1 and first paragraph match SEO plan.
- [ ] User can generate without login.
- [ ] User can copy main, short, and negative prompts.
- [ ] Empty, loading, success, error, and feedback states are designed.
- [ ] Token output includes top-down VTT-specific guidance.
- [ ] Feedback reason chips are available after negative feedback.
- [ ] Examples are crawlable and specific.
- [ ] FAQ is visible before FAQ JSON-LD is added.
- [ ] Footer links include About, Privacy, Terms, and Contact.
- [ ] Mobile layout works at 320px.
- [ ] Visual system avoids generic AI SaaS styling.
