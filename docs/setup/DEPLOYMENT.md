# TrendCipher — Deployment Guide

**Status:** verified 2026-10-18 (images built, stack run, healthchecks + API green)

This is the one-command path to run the whole product on a single machine —
backend API + ingestion worker + web (nginx) + persistent SQLite — with **no
paid resources**.

---

## Prerequisites

- Docker Engine + Docker Compose v2 (`docker compose version`).
- A domain/IP with ports **80** open (web) — backend stays internal.
- Optional: `openssl` to generate a `SECRET_KEY`.

## Quick start (recommended — Docker Compose)

```bash
# 1. Get the code
git clone https://github.com/alimazna/project.git
cd project

# 2. Configure environment
cp deploy/.env.example .env
#   EDIT .env → set a strong SECRET_KEY, CORS_ORIGINS, PUBLIC_BASE_URL
openssl rand -hex 32   # → paste the output into SECRET_KEY

# 3. Build and start everything
docker compose -f deploy/docker-compose.yml up -d --build

# 4. Verify
curl -fsS http://localhost/healthz            # {"status":"ok",...}
curl -fsS http://localhost/api/v1/plans       # seeded plans JSON
curl -fsS http://localhost/login              # 200 (SPA route)

# 5. Logs / stop
docker compose -f deploy/docker-compose.yml logs -f
docker compose -f deploy/docker-compose.yml down
```

The stack starts three services:

| Service | Container image | Exposes | Runs |
|---|---|---|---|
| `web` | `trendcipher-web` (nginx) | host port 80 | Vite static SPA + `/api` proxy |
| `backend` | `trendcipher-backend` | internal 8000 | FastAPI + SQLAlchemy + controller of health |
| `worker` | `trendcipher-backend` | — | `app.workers.ingestion` (candles/news/alerts loop) |

SQLite is persisted on the `trendcipher-data` volume (`/app/data/trendcipher.db`);
the worker and backend share the same volume so the DB is consistent.

## Configuration keys (from `deploy/.env.example`)

| Key | Default | Purpose |
|---|---|---|
| `SECRET_KEY` | placeholder **must change** | JWT signing — generate with `openssl rand -hex 32` |
| `CORS_ORIGINS` | `http://localhost` | Comma-separated browser origins allowed to call the API |
| `PUBLIC_BASE_URL` | `http://localhost` | Canonical public URL (used in links/redirects) |
| `DATABASE_URL` | `sqlite:////app/data/trendcipher.db` | Set by compose; swap to Postgres for scale |
| `MARKET_PROVIDER` | `kraken` | `kraken` primary, OKX fallback by default |
| `NEWS_FEEDS` | CoinTelegraph + CoinDesk | `url|name` pairs separated by commas |
| `PUSH_PROVIDER` | `log` | `log` (labeled stub, default) or `expo` (real service) |
| `INGESTION_LOOP_SECONDS` / `NEWS_LOOP_SECONDS` | 300 / 600 | Worker cadence |

> The web build bakes `VITE_API_BASE_URL=/api/v1` so the browser calls the same
> origin; nginx proxies `/api/*` → backend. No CORS issues on same origin.

## First user

The **first registered user** becomes `super_admin` automatically. Everything
else (plans seed, table creation) is handled by the backend lifespan hook.

## Reverse proxy / HTTPS (buyer decision)

For production, put a TLS terminator in front of port 80 (Caddy, Traefik, or
cloud LB). Recommended minimal Caddy directive:

```
yourdomain.com {
    reverse_proxy localhost:80
}
```

Keep `CORS_ORIGINS=https://yourdomain.com` and
`PUBLIC_BASE_URL=https://yourdomain.com` in `.env`, then `docker compose up -d`.

## Plain-process alternative (no Docker)

```bash
cd backend && pip install -e ".[dev]"

# Terminal 1 — API
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Terminal 2 — worker (candles/news/alerts loop)
python -m app.workers.ingestion

# Terminal 3 — web (dev) or build + serve statically
cd web && npm install && npm run dev
# production: npm run build && (serve web/dist with any static host + proxy /api → :8000)
```

## Verification status (honest)

- [x] `docker compose config` validates.
- [x] Both images build on this machine (backend `python:3.13-slim`, web multi-stage → nginx).
- [x] Stack runs; `backend` becomes healthy (healthcheck hits `/healthz`).
- [x] `http://localhost/healthz`, `/api/v1/plans`, `/login`, SPA assets all served through nginx.
- [x] Docker daemon is **not** part of CI; `security`/`licenses` jobs run on the
      workflow. The images above were built on the dev worker (2026-10-18) and
      should be kept in sync with each repo change.