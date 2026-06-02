# Docker Deployment

This directory contains the Nginx configuration used by the frontend container.
The deployment entry point is `../docker-compose.yml`.

## Quick Start

From the `dnd-prompt-forge` directory:

```bash
cp .env.example .env
```

Edit `.env` and set `DEEPSEEK_API_KEY` if you want LLM-powered generation.
Without an API key, the backend still starts and uses its deterministic fallback
prompt generator.

```bash
docker compose up --build -d
```

Open:

```text
http://localhost:8080
```

## Services

- `frontend`: Nginx static frontend, published on `FRONTEND_PORT` by default.
- `backend`: FastAPI backend, published on `BACKEND_PORT` by default.
- `backend-data`: Docker volume storing the SQLite database.

## Environment Variables

- `DEEPSEEK_API_KEY`: optional API key for DeepSeek.
- `DEEPSEEK_BASE_URL`: defaults to `https://api.deepseek.com/v1`.
- `DEEPSEEK_MODEL`: defaults to `deepseek-chat`.
- `LLM_TIMEOUT_SECONDS`: defaults to `30`.
- `DB_PATH`: defaults to `/app/data/prompt_forge.db`.
- `FRONTEND_PORT`: defaults to `8080`.
- `BACKEND_PORT`: defaults to `8000`.

## Useful Commands

```bash
docker compose ps
docker compose logs -f
docker compose down
```
