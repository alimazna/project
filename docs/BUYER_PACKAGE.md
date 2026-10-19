# TrendCipher — Buyer Ownership Package

Everything you need to own, run, rebrand, and sell this product. Verified state
at handover: **2026-10-18**, commit **ce52271** (see `HANDOFF.md`).

---

## 1. What you bought

- **Backend** — FastAPI + SQLAlchemy (SQLite→Postgres path), auth w/ refresh-token
  rotation, market/news ingestion, deterministic analysis engine (rule-versioned),
  alerts + push, admin panel, subscriptions/billing, health & smoke-suite.
- **Web** — React 18 + Vite SPA: landing, pricing, dashboard w/ charts
  (lightweight-charts), scanner, scenarios, watchlist, alerts, account, admin.
- **Mobile** — Expo SDK ~58 app: auth, dashboard, watchlist, scenarios, alerts,
  account (with expo-notifications push), asset & analysis detail screens.
- **Operations** — Docker Compose one-command deployment, backup/restore docs,
  secret-scan procedure, license inventories, CI (tests/security/licenses).

## 2. Quick start (10 minutes to seeing it live)

```bash
git clone <your-new-repo-url> && cd <repo>
cp deploy/.env.example .env             # edit SECRET_KEY + CORS_ORIGINS
openssl rand -hex 32                    # → paste into SECRET_KEY
docker compose -f deploy/docker-compose.yml up -d --build
open http://localhost/register           # first user = super_admin
```

Full version: `docs/setup/DEPLOYMENT.md` · plain-process variant included there.

## 3. The docs map

| When you need to… | Read |
|---|---|
| Deploy / HTTPS / ports | `docs/setup/DEPLOYMENT.md` |
| Rebrand the product | `docs/REBRAND.md` |
| Back up / restore data | `docs/setup/BACKUP_RECOVERY.md` |
| Scan for secrets before launch | `docs/setup/SECRET_SCAN.md` |
| Check third-party licenses | `docs/licenses/LICENSE_SUMMARY.md` |
| Understand the architecture | `docs/architecture/MASTER_ARCHITECTURE.md` + `ARCHITECTURE_DECISIONS.md` |
| Change analysis rules | `docs/architecture/ANALYTICAL_ENGINE.md` |
| Understand data providers | `docs/architecture/DATA_PROVIDERS_AND_LICENSING.md` |
| Plan product roadmap | `docs/architecture/IMPLEMENTATION_ROADMAP.md` |
| Debug a hot issue | `HANDOFF.md` (living log) + `docs/architecture/SECURITY_AND_PRIVACY.md` |
| Start a support conversation | `docs/architecture/SALES_READINESS_PLAN.md` §Waves |

> All paths are relative to the repository root.

## 4. Non-negotiables before production

1. **Change `SECRET_KEY`** — it signs JWTs. `openssl rand -hex 32`.
2. **Put HTTPS in front** (Caddy/Traefik/cloud LB) — see `DEPLOYMENT.md`.
3. **Run the secret scan** (`docs/setup/SECRET_SCAN.md`) — last run: 0 findings.
4. **Back up the SQLite volume** daily (`docs/setup/BACKUP_RECOVERY.md`).
5. **Register a real domain + rename repo** — brand is config-driven, repo name isn't.

## 5. What is NOT included (honest list)

- **Real push delivery**: default `PUSH_PROVIDER=log` is a labeled stub. Setting it
  to `expo` requires an Expo account token + Apple/Google dev accounts + a physical
  device test. (Backend logs requests today; wiring exists.)
- **Store publishing (Google Play / App Store)**: intentionally out of scope — the
  product ships **web-first**, and the mobile app runs via **Expo Go** or a side-loaded
  APK (see `docs/setup/EXPO_GO_HOWTO.md`). No Apple/Google developer accounts needed.
- **CI on your account**: `.github/workflows/ci.yml` will run once the repo is under
  your GitHub namespace (standard Actions quota).
- **Postgres hosting**: SQLite works and is default; scaling to PG is buyer-side.

## 6. Skeleton of the repo

```
backend/    FastAPI app + tests (136 passing) + ingestion worker
web/        React SPA + vitest (11 passing) + eslint/tsc clean
mobile/     Expo app (tsc clean) — auth, tabs, detail screens, push
deploy/     Dockerfiles, nginx config, compose stack, .env.example
docs/       architecture + setup/operator + licenses + buyer docs
scripts/    smoke_test.py (36-step API E2E journey)
.github/    CI workflow (backend, web, security)
```

## 7. Getting support / extending

- All tests pass out of the box: backend `cd backend && python -m pytest -q`
  (136), web `cd web && npx vitest run` (11), mobile `cd mobile && npx tsc --noEmit`.
- The project was co-created by an AI agent (OpenHands) on behalf of the owner;
  the full history and decisions are in `docs/architecture/ARCHITECTURE_DECISIONS.md`.