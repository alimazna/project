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

## Mobile (Expo) — Stage 6
- Project at `mobile/` (Expo SDK ~58, expo-router, React 19, RN 0.88).
- Commands: `cd mobile && npx tsc --noEmit` (typecheck), `npx eslint .` (lint; also `npx expo lint` configures eslint), `npx expo-doctor`, `npx expo export --platform android` (bundle check).
- `npm install`/`npx expo install` — always use `npx expo install` for SDK-compatible versions. Pin `react-dom@19.3.0` to match Expo SDK 58 expectation (transitive `react-dom@19.3.1` requires `react@^19.3.1` — conflicts).
- Deps added: `@expo/vector-icons`, `expo-font`, `react-native-svg` (transitive), `expo-notifications`, `expo-secure-store`, `expo-constants`.
- API base configurable via `EXPO_PUBLIC_API_BASE_URL` (default `http://localhost:8000/api/v1`); `.env.example` documents it.
- eslint hook rule `react-hooks/set-state-in-effect` flags direct `load()` in effects — use the async-IIFE pattern `(async () => { await load(); })().catch(() => undefined);`.
- `AndroidImportance.HIGH` (value 6) referenced as numeric constant `CHANNEL_IMPORTANCE_HIGH` to avoid the eslint `import/namespace` deep-path resolver failure.
- Routes guarded by auth: tabs layout and standalone asset/analysis screens redirect to `/login` when no token.

## Current stage
**Product COMPLETE + Sales Readiness Waves 1–6 ALL DONE and pushed on `main`.**
Remote `main` chain (all certified green): `f8549e5` (compose deploy, live-verified)
→ `2aaa092` (rebrand) → `e171d27` (ops/secret-scan/licenses) → `ce52271` (web tests
11/11) → `d4c922b` (buyer package) → Wave 6 final (repo index + close-out).

> **BEFORE doing anything: read `docs/architecture/EXECUTION_PLAN.md` — it is the
> authoritative loop-proof task list with exact commands and DoD checks. Follow
> §1 operating rules (time boxes, no scope creep, verify-before-DONE) and never
> touch §6 Deferred items without the user's explicit instruction.**
>
> **SALE READINESS is FINISHED:** the authoritative add-on plan
> `docs/architecture/SALES_READINESS_PLAN.md` (Waves 0–6) is fully executed and
> verified. The buyer-facing entry point is `docs/BUYER_PACKAGE.md`; launch gate
> is `docs/RELEASE_CHECKLIST.md`. Only buyer-side decisions remain (domain, TLS,
> push accounts, EAS build) — never invent them, ask the owner.

What remains (non-blocking, buyer-scoped):
- Real push E2E: physical device + platform accounts (`PUSH_PROVIDER=expo`).
- Mobile binaries via EAS under a buyer's own Apple/Google accounts.
- Postgres deployment if the buyer outgrows SQLite (documented path).
- Terms/privacy pages + legal review before a public launch (per RELEASE_CHECKLIST).