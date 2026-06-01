# DND Character Prompt Generator PRD

Date: 2026-06-01
Status: Draft for implementation
Product type: SEO landing application + free prompt tool
Primary business goal: Build a 1-2 day MVP that can attract long-tail Google SEO traffic and later monetize with Google AdSense.

## 1. Product Summary

DND Character Prompt Generator is a free landing application that helps Dungeons & Dragons players and Dungeon Masters turn character ideas into copy-ready AI image prompts.

The first MVP does not generate images. It generates structured prompts for tools such as ChatGPT image generation, Midjourney, Gemini, Leonardo, Stable Diffusion, and other image models.

Core promise:

```text
Turn your DND character idea into a copy-ready AI image prompt for portraits, tokens, monsters, NPCs, and fantasy scenes.
```

## 2. Target Users

### Primary users

- DND players who want a portrait for their own character.
- Dungeon Masters who need NPCs, monsters, scenes, and VTT tokens.
- Online tabletop users using Roll20, Foundry VTT, D&D Beyond, Fantasy Grounds, or similar tools.

### Secondary users

- Fantasy writers.
- Indie game designers.
- AI art users who need better fantasy character prompts.

## 3. User Pain Points

- Users have a character idea but cannot express it as a good English AI image prompt.
- DND settings have many visual variables: race, class, alignment, armor, weapon, spell, background, mood, pose, style.
- Generic AI image tools do not guide users through DND-specific details.
- Direct AI image generators may require login, credits, payment, or model lock-in.
- Dungeon Masters often need many assets quickly, not one expensive perfect image.
- Top-down tokens, portraits, full-body art, monsters, and scenes need different prompt structures.

## 4. MVP Scope

### In scope

- SEO landing homepage.
- Free DND prompt generator form.
- DeepSeek LLM API integration through a simple Python backend.
- Prompt output for:
  - Character portrait.
  - Full-body character art.
  - Top-down VTT token.
  - NPC.
  - Monster.
  - Fantasy scene.
- Negative prompt generation.
- Copy-to-clipboard.
- Regenerate prompt.
- User feedback buttons: useful / not useful.
- Negative feedback memory capture.
- Automatic self-correction on later generations within the same product system.
- Static pages:
  - About Us.
  - Privacy Policy.
  - Terms.
  - Contact.
- SEO metadata and structured data plan.

### Out of scope for MVP

- Direct image generation.
- User accounts.
- Payment.
- Saved prompt library.
- Uploading character sheets.
- Full campaign builder.
- Real-time collaboration.
- Complex admin dashboard.

## 5. Core User Flow

1. User lands on SEO page from Google.
2. User sees the tool immediately above the fold.
3. User selects output type: portrait, token, NPC, monster, scene.
4. User fills basic DND details.
5. User clicks generate.
6. Python backend sends structured request to DeepSeek.
7. LLM returns:
   - Main prompt.
   - Short prompt.
   - Negative prompt.
   - Style notes.
   - Optional backstory seed.
8. User copies prompt.
9. User marks the result as useful or not useful.
10. If not useful, user selects or writes why.
11. System stores feedback memory and uses it to adjust future prompt generation.

## 6. UI Layout

### Global layout

- Header:
  - Logo/name: DND Prompt Forge
  - Navigation: Character Prompt, Token Prompt, Monster Prompt, Scene Prompt, About, Contact
- Main content:
  - Hero/tool area.
  - Generator form.
  - Output panel.
  - Examples.
  - How it works.
  - FAQ.
- Footer:
  - About Us
  - Privacy Policy
  - Terms
  - Contact

### Homepage first viewport

H1:

```text
DND Character Prompt Generator
```

Supporting copy:

```text
Create copy-ready AI image prompts for DND characters, NPCs, monsters, tokens, and fantasy scenes. Free, no login required.
```

Tool should appear in the first viewport, not below a marketing-only hero.

### Generator form fields

Required fields:

- Output type:
  - Character portrait
  - Full-body character
  - Top-down VTT token
  - NPC
  - Monster
  - Scene
- Race / creature type
- Class / role
- Visual style
- Mood
- Short description

Optional fields:

- Gender presentation
- Age
- Alignment
- Armor
- Weapon
- Magic/spell theme
- Background setting
- Color palette
- Camera angle
- Model target:
  - Midjourney
  - ChatGPT
  - Gemini
  - Leonardo
  - Stable Diffusion
  - General purpose

### Output panel

Output blocks:

- Main prompt.
- Short prompt.
- Negative prompt.
- Token-specific notes when output type is token.
- Copy buttons for each block.
- Regenerate button.
- Feedback:
  - Useful
  - Not useful
  - Feedback reason:
    - Too generic
    - Not DND-specific enough
    - Wrong style
    - Missing details
    - Too long
    - Too short
    - Other

## 7. LLM Behavior

### DeepSeek API role

DeepSeek is used to transform structured user inputs into high-quality, model-ready English prompts.

The backend should send a structured prompt instruction that includes:

- Output type.
- DND entity details.
- Target AI model.
- Style constraints.
- Safety constraints.
- Feedback memory summary when available.

### LLM output format

The backend should request JSON:

```json
{
  "main_prompt": "...",
  "short_prompt": "...",
  "negative_prompt": "...",
  "style_notes": "...",
  "usage_tip": "..."
}
```

### Quality rules

Generated prompts should:

- Be written in clear English.
- Include DND-specific visual details.
- Avoid copyrighted character names unless supplied by the user as their own reference.
- Avoid explicit sexual content.
- Avoid hateful or extremist visual framing.
- Avoid medical, legal, or financial advice.
- Avoid claiming that output images are guaranteed.

## 8. Self-Iteration And Feedback Memory

### Goal

When users give negative feedback, the system should learn lightweight correction rules and apply them to future generations.

This is not a full training pipeline. It is product-level memory and prompt adaptation.

### Feedback memory events

Record:

- Timestamp.
- Input fields.
- Generated output.
- Feedback type: useful / not useful.
- Negative feedback reason.
- Optional user comment.
- Current prompt template version.
- Current correction rules used.

### Memory storage for MVP

Simple options:

- SQLite database.
- JSONL file.

Recommended MVP:

- SQLite for structured feedback.
- A small `memory_rules` table for active correction rules.

### Self-correction mechanism

1. Store every negative feedback event.
2. Periodically or immediately summarize patterns:
   - Too generic.
   - Missing race details.
   - Token prompts not top-down enough.
   - Negative prompt too weak.
   - Prompt too long.
3. Convert repeated patterns into correction rules.
4. Add active correction rules into future DeepSeek system prompt.
5. Track rule version.

### Example correction rule

```text
If output_type is top-down token, always mention top-down view, centered full-body silhouette, transparent or simple background, readable outline, and VTT token usability.
```

### Acceptance criteria

- User can mark a prompt as not useful.
- Negative reason is stored.
- Future LLM calls include a compact memory summary.
- Admin or developer can inspect feedback logs.
- Prompt template version is visible in logs.

## 9. Static Pages

### About Us

Purpose:

- Explain that the site helps DND players and DMs create better AI image prompts.
- Mention it is free and no-login for MVP.
- Avoid exaggerated claims.

Required sections:

- What this tool does.
- Who it is for.
- What it does not do.
- How feedback improves the prompt engine.

### Privacy Policy

Required points:

- What user inputs are collected.
- Feedback and generated prompt logs may be stored to improve the tool.
- No account required in MVP.
- Contact email.
- Cookies/analytics disclosure if used.
- AdSense disclosure once ads are enabled.

### Terms

Required points:

- Tool is provided as-is.
- Generated prompts are not guaranteed to produce a specific image.
- Users are responsible for how they use prompts in third-party tools.
- No illegal, hateful, explicit, or infringing use.
- DND is a trademark of its respective owner; site should avoid implying official affiliation.

### Contact

Required points:

- Contact form or email.
- Bug report option.
- Feedback option.
- Removal or privacy request option.

## 10. Success Metrics

### Product metrics

- Prompt generation completion rate.
- Copy button click rate.
- Useful feedback rate.
- Negative feedback reason distribution.
- Repeat generation rate.

### SEO metrics

- Indexed pages.
- Impressions by page.
- CTR.
- Query positions.
- Pages with impressions but low CTR.

### Business metrics

- Daily organic visitors.
- AdSense page RPM once enabled.
- Pages per session.
- Returning visitors.

## 11. Implementation Acceptance Criteria

- Homepage loads fast on mobile.
- Tool is usable without login.
- DeepSeek API generation works through Python backend.
- Errors are shown clearly when API fails.
- Feedback can be recorded.
- Negative feedback can influence later prompt generation through memory rules.
- About, Privacy Policy, Terms, Contact pages exist and are linked in footer.
- Basic SEO metadata exists.
- JSON-LD exists for SoftwareApplication and FAQPage when FAQ is visible.
- Sitemap and robots are planned or implemented before public launch.

