# TrendCipher — Repository Memory

## Project
Explainable cryptocurrency market-intelligence product (news intelligence + deterministic technical analysis). Backend (FastAPI) + Web (React/TS/Vite) + Mobile (Expo, planned).

## Per user instruction — checkpoint discipline
"كل مهمة تقوم بها ادفعها ع جيتهوب" — commit + push every completed step to GitHub:
`git add -A && git commit -m "..." && git push https://$PAT@github.com/alimazna/project.git main`
(Push needs explicit auth with the user's PAT; repo remote stored without token.)

## Commands
- Backend tests: `cd backend && python -m pytest -q`
- Backend lint: `cd backend && python -m ruff check app tests`
- Backend serve: `cd backend && python -m uvicorn app.main:app --port 8000`
- Web build: `cd web && npm run build`  (typecheck = `npx tsc -b`)
- Web tests: `cd web && npx vitest run`

## Stack & key facts
- Python 3.13, FastAPI, SQLAlchemy 2, pydantic v2, argon2-cffi, PyJWT; pytest + ruff.
- Node 24, Vite 5 + React 18 + TS; lightweight-charts (Apache 2.0); vitest + testing-library.
- SQLite default (`.env`/`DATABASE_URL`); models support Postgres upgrade path.

## Providers / licensing (research findings)
- Binance & Bybit geo-blocked (403). Working: **Kraken** (OHLC), **Coinbase**, **CoinGecko** (ping/trending/simple price), **OKX** (spot ticker), **KuCoin** (time).
- News: **CoinTelegraph RSS**, **CoinDesk RSS** (308 redirect to coindesk.com). `feedparser`.
- Charts: TradeView Lightweight Charts = Apache 2.0 (redistribution OK with license notice).
- Push notifications planned via `expo-notifications`.
- Full analysis: `docs/architecture/*.md` + `HANDOFF.md` + `README.md`.

## Architecture decisions (see docs/architecture/ARCHITECTURE_DECISIONS.md)
- News = evidence, not prediction. Analysis determinism: closed candles only, rule-versioned engine, evidence lists with source attribution.
- Auth: first registered user becomes `super_admin`; roles user/admin/super_admin; refresh-token rotation.
- Ruff ignores E501 + B008 (FastAPI `Depends()` idiom is intentional).
- SQLite returns naive datetimes — normalize with `_as_utc()` before comparing to aware UTC.

## Current stage
Stage 2 (foundation) DONE: backend auth module + web skeleton committed (`255de31`, on origin/main). Next per IMPLEMENTATION_ROADMAP:
- Admin routes (plans CRUD admin) — Stage: analytics engine & news intelligence modules, market provider adapters, ingestion workers, then charts dashboard, mobile, Docker/CI.