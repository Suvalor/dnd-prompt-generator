# DND Character Prompt Generator SEO Plan

Date: 2026-06-01
Status: Draft for implementation
SEO standard referenced: `/Users/suycity/Workspace/01 学习笔记/seo-rules.md`

## 1. SEO Principle

This site should not be written as a brand ad first.

Every page should answer a real search intent:

- "I need a DND character prompt."
- "I need a DND token prompt."
- "I need a Tiefling Warlock portrait prompt."
- "I need a prompt for a DND monster or NPC."

Brand and conversion sections should support that intent.

## 2. Homepage SEO

### Primary keyword

```text
DND Character Prompt Generator
```

### Supporting long-tail keywords

- DND character prompt
- DND portrait prompt generator
- DND AI image prompt
- DND token prompt generator
- DND NPC prompt generator
- DND monster prompt generator
- fantasy character prompt generator
- DND character image prompt
- tabletop RPG character prompt
- VTT token prompt

### Title

```text
DND Character Prompt Generator | Free AI Image Prompts
```

### Meta description

```text
Create copy-ready AI image prompts for DND characters, NPCs, monsters, tokens, and fantasy scenes. Free DND prompt generator, no login required.
```

### H1

```text
DND Character Prompt Generator
```

### First paragraph requirement

The first paragraph should include the primary keyword naturally and explain the concrete outcome.

Example:

```text
Use this DND Character Prompt Generator to turn your race, class, style, weapon, and backstory idea into a copy-ready AI image prompt for portraits, VTT tokens, NPCs, monsters, and fantasy scenes.
```

## 3. Homepage H2 Structure

Recommended H2s:

- Create DND Character Prompts For Any AI Image Tool
- Generate Portraits, Tokens, NPCs, Monsters, And Scenes
- How The DND Prompt Generator Works
- Example DND Character Prompts
- Who This Tool Is For
- DND Prompt Generator FAQ

## 4. Landing Page Content Blocks

### Above the fold

- H1 with primary keyword.
- One-sentence value proposition.
- Generator form.
- No marketing-only hero that hides the tool.

### Examples section

Include concrete generated examples:

- Tiefling Warlock portrait prompt.
- Elf Ranger full-body prompt.
- Dragonborn Paladin token prompt.
- Goblin merchant NPC prompt.
- Haunted tavern scene prompt.

### Data/workflow limitation section

Explain:

- The tool generates prompts, not final images.
- Output quality depends on the third-party AI image model.
- Users can copy prompts into their preferred image tool.

## 5. Structured Data

Add JSON-LD when visible content exists:

### `SoftwareApplication`

Use for homepage/tool page:

- Name: DND Character Prompt Generator
- Application category: DesignApplication or UtilitiesApplication
- Operating system: Web
- Offers: Free

### `Organization`

Use for site identity:

- Name: DND Prompt Forge
- URL: canonical domain
- Contact point if available

### `FAQPage`

Use only when FAQ is visible on the page.

FAQ candidates:

- What is a DND character prompt generator?
- Does this tool generate images?
- Can I use these prompts in Midjourney or ChatGPT?
- Can it create top-down VTT token prompts?
- Is the DND prompt generator free?
- Do I need to log in?

## 6. Initial Public Routes

### Core pages

| Route | Primary keyword |
| --- | --- |
| `/` | DND Character Prompt Generator |
| `/dnd-token-prompt-generator` | DND Token Prompt Generator |
| `/dnd-monster-prompt-generator` | DND Monster Prompt Generator |
| `/dnd-npc-prompt-generator` | DND NPC Prompt Generator |
| `/dnd-scene-prompt-generator` | DND Scene Prompt Generator |
| `/fantasy-character-prompt-generator` | Fantasy Character Prompt Generator |

### Long-tail pages

| Route | Primary keyword |
| --- | --- |
| `/tiefling-warlock-prompt-generator` | Tiefling Warlock Prompt Generator |
| `/elf-ranger-prompt-generator` | Elf Ranger Prompt Generator |
| `/dragonborn-paladin-token-prompt` | Dragonborn Paladin Token Prompt |
| `/dnd-tavern-scene-prompt` | DND Tavern Scene Prompt |
| `/dnd-villain-prompt-generator` | DND Villain Prompt Generator |
| `/dnd-cleric-portrait-prompt` | DND Cleric Portrait Prompt |
| `/dnd-rogue-character-prompt` | DND Rogue Character Prompt |
| `/dnd-wizard-character-prompt` | DND Wizard Character Prompt |
| `/dnd-bard-character-prompt` | DND Bard Character Prompt |
| `/dnd-druid-character-prompt` | DND Druid Character Prompt |

Rule:

- Each page must have exactly one primary keyword.
- Do not target multiple unrelated keywords on one page.

## 7. Page Template For Long-Tail SEO

Each long-tail page should include:

- Unique title.
- Unique meta description.
- One H1 matching primary intent.
- Tool pre-filled or scoped to the page topic.
- Example prompt.
- Tips specific to that race/class/output type.
- FAQ.
- Internal links to related pages.

Example page:

```text
Primary keyword: Tiefling Warlock Prompt Generator
H1: Tiefling Warlock Prompt Generator
H2: Create A Tiefling Warlock Portrait Prompt
H2: What Details Make A Tiefling Warlock Prompt Better?
H2: Example Tiefling Warlock Prompt
H2: Related DND Character Prompt Tools
```

## 8. Internal Linking

Footer links:

- Character Prompt Generator
- Token Prompt Generator
- Monster Prompt Generator
- NPC Prompt Generator
- Scene Prompt Generator
- About
- Privacy Policy
- Terms
- Contact

Content links:

- Homepage links to all core pages.
- Core pages link to 5-10 relevant long-tail pages.
- Long-tail pages link back to homepage and sibling race/class pages.

Avoid:

- Permanent coming-soon links.
- Important SEO links hidden in JS-only UI.

## 9. Technical SEO Requirements

Required before public launch:

- `robots.txt`
- `sitemap.xml`
- Canonical URL on every public page.
- Unique `title`.
- Unique `meta description`.
- Open Graph title and description.
- Twitter card title and description.
- Semantic H1/H2 structure.
- Crawlable anchor links.
- Mobile-friendly layout.
- No `meta keywords` tag.
- No keyword stuffing.

Recommended rendering:

- Prefer static HTML, SSG, SSR, or pre-rendering.
- Avoid pure client-rendered SEO pages if practical.

## 10. AdSense Readiness

Required content pages:

- About Us.
- Privacy Policy.
- Terms.
- Contact.

Ad placement for MVP:

- Do not overload the first viewport.
- Place ads after useful content exists.
- Avoid layout shifts.
- Keep generator usable without ad obstruction.

AdSense-safe content rules:

- Avoid explicit sexual content.
- Avoid hateful, violent extremist, or illegal content.
- Avoid copyrighted character generation claims.
- Add trademark disclaimer for DND if needed.

## 11. Search Console Iteration

Review monthly after launch:

- High impressions + CTR below 2%: rewrite title/meta description.
- Ranking 4-10: improve depth, examples, and internal links.
- Indexed but no clicks: check intent mismatch.
- Not indexed: check sitemap, canonical, robots, and render output.

## 12. SEO Launch Checklist

- [ ] Homepage primary keyword defined.
- [ ] Supporting keywords defined.
- [ ] H1 includes primary keyword.
- [ ] Title and meta description unique.
- [ ] Canonical present.
- [ ] OG/Twitter metadata present.
- [ ] FAQ answers real search questions.
- [ ] JSON-LD matches visible content.
- [ ] Page explains prompt workflow and limitations.
- [ ] No meta keywords tag.
- [ ] No keyword stuffing.
- [ ] Sitemap includes real routes.
- [ ] Robots allows public routes.
- [ ] Search Console ready.

