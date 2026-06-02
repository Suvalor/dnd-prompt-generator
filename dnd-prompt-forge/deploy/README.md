# Docker Deployment

This directory contains the Nginx configuration used by the frontend container.
The deployment entry point is the repository root `docker-compose.yml`.

## Quick Start

From the repository root:

```bash
cp .env.example .env
```

Edit `.env` only if you want to change the public frontend port.

```bash
docker compose up --build -d
```

Open:

```text
http://localhost:8081
```

## Services

- `frontend`: Nginx static frontend, published on `FRONTEND_PORT` by default.

The FastAPI backend code remains in `../backend/`, but this static deployment
does not start it. The current frontend generates prompts in the browser.

## Environment Variables

- `FRONTEND_PORT`: defaults to `8081`.

## Useful Commands

```bash
docker compose ps
docker compose logs -f
docker compose down
```
