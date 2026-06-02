# DND Prompt Forge App

This directory contains the DND Prompt Forge web application.

## What It Does

DND Prompt Forge helps tabletop players and dungeon masters turn character or scene ideas into copy-ready AI image prompts. The frontend currently supports browser-side deterministic prompt generation, including positive prompts, negative prompts, short prompts, style notes, and usage tips.

## Structure

```text
dnd-prompt-forge/
├── frontend/           # Static HTML/CSS/JS frontend
├── backend/            # FastAPI backend for API and LLM experiments
├── deploy/             # Nginx config and deployment notes
└── docs/               # App-specific working docs
```

## Frontend

The frontend is a static web app:

```bash
cd frontend
python3 -m http.server 8081
```

## Backend

The backend is retained for API, LLM, feedback, quota, and multimodal work:

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Provider API keys must only be configured on the backend. Do not expose them in frontend files.

## Deployment

Use the repository root `docker-compose.yml` for Docker deployment:

```bash
cd ..
docker compose up -d --build
```

See `deploy/README.md` for deployment details.

## Usage Rules

This app is for non-commercial use only. You may use, study, modify, and share it for personal, educational, and research use. You may not sell it, host it as a paid service, bundle it into a commercial product, or use provider credentials in ways that violate provider terms.

See the repository root `README.md` for the full non-commercial usage notice.
