# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**DND Prompt Forge** — A free SEO landing application that generates copy-ready AI image prompts for D&D characters, tokens, NPCs, monsters, and fantasy scenes. Built as a 1-2 day MVP experiment targeting long-tail Google SEO traffic with future Google AdSense monetization.

- **Product**: DND Character Prompt Generator
- **Experiment ID**: 003
- **Primary Keyword**: "DND Character Prompt Generator"
- **Domain**: dndpromptforge.com (planned)

## Repository Structure

```
/workspace/
├── src/                          # Source code (to be implemented)
├── data/                         # Runtime data / SQLite database
├── output/                       # Generated outputs
├── docs/                           # Planning documents
│   ├── 20260601-ui-outline.md
│   ├── 20260601-adsense-seo-mvp-keyword-research.md
│   └── scope-change/
│       ├── 20260601-dnd-prompt-generator-prd.md
│       ├── 20260601-dnd-prompt-generator-dev-doc.md
│       └── 20260601-dnd-prompt-generator-seo-plan.md
├── DND_Prompt_Forge_(standalone).html   # Standalone frontend (bundled)
├── extracted_template.html              # Extracted template version
├── PLAN.md                       # Experiment plan
├── RESULT.md                     # Experiment results (not started)
├── README.md                     # Project overview
└── notes.md                      # Project notes
```

## Architecture

### Frontend
- **Current**: Single-page static HTML with embedded CSS/JS
- **Planned**: Python FastAPI backend with static HTML frontend
- **Design System**: "Practical fantasy workshop" — warm parchment base, brass primary, crimson/emerald accents
- **Key Files**:
  - `DND_Prompt_Forge_(standalone).html` — Bundled standalone version with all assets inline
  - `extracted_template.html` — Extracted template with external script references

### Backend (Planned)
- **Framework**: Python FastAPI
- **Database**: SQLite for feedback memory
- **LLM**: DeepSeek API for prompt generation
- **Key Endpoints**:
  - `POST /api/generate-prompt` — Generate DND prompts
  - `POST /api/feedback` — Store user feedback
  - `GET /api/health` — Health check

### Data Model
- `prompt_requests` — Stores generation requests
- `feedback_events` — Stores user feedback
- `memory_rules` — Active correction rules from negative feedback

## Development Commands

### Frontend
```bash
# Serve the standalone HTML locally
python -m http.server 8000

# Or open directly
open DND_Prompt_Forge_\(standalone\).html
```

### Backend (when implemented)
```bash
# Install dependencies
pip install fastapi uvicorn sqlite3

# Run development server
uvicorn main:app --reload --port 8000

# Run with specific host
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Key Technical Details

### SEO Requirements
- Every page must have unique title, meta description, canonical URL
- JSON-LD structured data: `SoftwareApplication`, `FAQPage`, `Organization`
- Semantic H1/H2 structure with primary keyword
- Sitemap and robots.txt required before launch
- No `meta keywords` tag, no keyword stuffing

### LLM Integration
- **Provider**: DeepSeek
- **Output Format**: JSON with `main_prompt`, `short_prompt`, `negative_prompt`, `style_notes`, `usage_tip`
- **Environment Variables**: `DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`, `DEEPSEEK_MODEL`
- **Timeout**: 20-40 seconds, retry once on transient failures

### Feedback Memory System
- Stores negative feedback in SQLite
- Maps feedback reasons to correction rules:
  - "Too generic" → Add more race/class/gear-specific detail
  - "Not DND-specific enough" → Add tabletop fantasy terms
  - "Wrong style" → Prioritize selected style
  - "Missing details" → Use all non-empty user fields
  - "Too long" / "Too short" → Adjust prompt length
  - "Token not usable" → Force top-down, centered, readable silhouette

### Theme System
- **Classes**: `theme-forge`, `texture-on`, `accent-brass`, `accent-crimson`, `accent-forest`
- **Typography**: Cormorant Garamond (serif) for display, sans-serif for body
- **Colors**: Warm parchment (#F4EEDF), charcoal ink, brass/gold primary

## Planned Routes

### Core Pages
- `/` — Homepage with generator
- `/dnd-character-prompt-generator` — Character portrait
- `/dnd-token-prompt-generator` — VTT tokens
- `/dnd-monster-prompt-generator` — Monsters/NPCs
- `/dnd-scene-prompt-generator` — Fantasy scenes

### Long-tail SEO Pages
- `/tiefling-warlock-prompt-generator`
- `/elf-ranger-prompt-generator`
- `/dragonborn-paladin-token-prompt`
- `/dnd-tavern-scene-prompt`
- (And 10+ more race/class combinations)

### Utility Pages
- `/about` — About Us
- `/privacy` — Privacy Policy
- `/terms` — Terms of Service
- `/contact` — Contact

## Important Files to Reference

- **`docs/scope-change/20260601-dnd-prompt-generator-prd.md`** — Product requirements
- **`docs/scope-change/20260601-dnd-prompt-generator-dev-doc.md`** — Development document
- **`docs/scope-change/20260601-dnd-prompt-generator-seo-plan.md`** — SEO strategy
- **`docs/20260601-ui-outline.md`** — UI design specifications
- **`PLAN.md`** — Experiment plan and checklist
- **`RESULT.md`** — Experiment results (to be filled)

## Current Status

- ✅ Planning documents complete
- ✅ Frontend UI designed (standalone HTML)
- ✅ SEO strategy defined
- ❌ Backend API not yet implemented
- ❌ DeepSeek integration not yet implemented
- ❌ Feedback memory system not yet implemented
- ❌ Long-tail pages not yet created
- ❌ Sitemap/robots.txt not yet created

## Notes

- The standalone HTML file contains all assets inline (fonts, CSS, JS) for easy deployment
- The extracted template references external Babel scripts for development
- No build system is currently configured — everything is static HTML
- The project is designed as a lightweight MVP — avoid over-engineering
