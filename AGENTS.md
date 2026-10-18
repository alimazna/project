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
- CI: `.github/workflows/ci.yml` — backend pytest+ruff, web build+eslint+vitest, license report (pip-licenses + npm ls) on push/PR.

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
Backend (auth, providers, ingestion, analysis engine, admin) + web product (dashboard, scanner, scenarios, watchlist, alerts, account, admin) DONE. Latest commit on origin/main: `021bf30` (feat(admin): system overview — Stage 5f). CI workflow added (`.github/workflows/ci.yml`). Next per IMPLEMENTATION_ROADMAP:
- CI verified green on GitHub (after first push).
- Stage 4 remaining polish (charts/watchlist already present — full acceptance pass pending).
- Stage 6 mobile (Expo) + push, Stage 7 validation/handover.