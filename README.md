# DND Prompt Forge

DND Prompt Forge is a free, non-commercial tabletop utility that turns Dungeons & Dragons character, NPC, monster, token, and scene ideas into copy-ready AI image prompts.

The current frontend can generate prompts directly in the browser with deterministic rules. A FastAPI backend is also included for API and LLM experiments, quota control, and future multimodal work.

## Features

- Prompt generation for portraits, full-body characters, VTT tokens, NPCs, monsters, and scenes.
- Positive prompt, short prompt, negative prompt, style notes, and usage tips.
- One-click copy for individual prompts and complete positive + negative prompt output.
- Static frontend built with HTML, CSS, React UMD, Babel, and Lucide icons.
- SEO-ready pages with metadata, sitemap, robots.txt, and structured data.
- Optional FastAPI backend for future LLM, feedback, and quota-controlled API flows.
- Docker Compose deployment support.

## Project Structure

```text
.
├── docker-compose.yml              # Docker deployment entry point
├── .env.example                    # Example deployment environment variables
├── dnd-prompt-forge/
│   ├── frontend/                   # Static web app
│   ├── backend/                    # FastAPI backend, optional for current frontend
│   ├── deploy/                     # Nginx and deployment docs
│   └── README.md                   # App-level notes
├── docs/                           # Research and scope-change documents
├── PLAN.md
└── RESULT.md
```

## Quick Start

### Static Frontend Only

The frontend can be served by any static web server:

```bash
cd dnd-prompt-forge/frontend
python3 -m http.server 8081
```

Open:

```text
http://localhost:8081
```

### Docker Compose

From the repository root:

```bash
cp .env.example .env
docker compose up -d --build
```

Default ports:

- Frontend: `http://localhost:8081`
- Backend API: `http://localhost:8002`

Useful commands:

```bash
docker compose ps
docker compose logs -f
docker compose down
```

## Environment Variables

```text
FRONTEND_PORT=8081
BACKEND_PORT=8002
MIMO_API_KEY=
MIMO_BASE_URL=https://api.xiaomimimo.com/v1
MIMO_MODEL=mimo-v2.5
LLM_TIMEOUT_SECONDS=60
LOG_LEVEL=INFO
SESSION_COOKIE_SECRET=
CSRF_SECRET=
DB_PATH=/app/data/prompt_forge.db
```

If no LLM API key is configured, the backend should fall back to deterministic prompt generation where supported.

## Backend Notes

The backend code is kept in `dnd-prompt-forge/backend/`.

Current and planned API responsibilities include:

- Prompt generation endpoint.
- Feedback endpoint.
- Health check.
- Future LLM provider integration.
- Future quota control and abuse protection.
- Future image/video understanding support.

The frontend must never expose provider API keys. Any LLM or multimodal provider call must go through the backend with server-side quota and credential controls.

## Non-Commercial Use Only

This project is released for learning, personal, research, and non-commercial tabletop use only.

You may:

- Read, fork, study, and modify the code.
- Run the project for personal campaigns, demos, education, and research.
- Share non-commercial derivatives with attribution.

You may not:

- Sell this project or a derivative product.
- Offer it as a paid SaaS, hosted product, marketplace tool, or commercial API.
- Bundle it into a commercial product or paid template.
- Use the project branding, UI, prompt rules, or generated product concept for commercial resale.
- Use third-party LLM credentials, subscription plans, or token plans in ways that violate the provider's terms.

For commercial licensing or permission, contact the project owner before use.

## Third-Party Services

If you connect an LLM or multimodal provider, you are responsible for:

- Complying with that provider's terms.
- Using credentials that are allowed for your deployment scenario.
- Keeping API keys secret.
- Applying rate limits and abuse protection.
- Reviewing generated content before publication or downstream use.

Do not simulate, spoof, or misrepresent the calling environment to bypass provider usage restrictions.

## Development Notes

- Keep the deterministic frontend generator available as the fallback path.
- Treat backend LLM calls as optional and quota-controlled.
- Keep generated databases, virtual environments, caches, and local secrets out of git.
- Put implementation-driving requirement changes under `docs/scope-change/`.

## License

Non-commercial source-available license.

Copyright (c) 2026.

Permission is granted to use, copy, modify, and share this project for personal, educational, research, and other non-commercial purposes only. Commercial use is prohibited without prior written permission from the project owner.
