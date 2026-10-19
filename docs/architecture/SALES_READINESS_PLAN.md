# TrendCipher — Sales-Readiness Plan (أكمل مشروع ممكن + جاهزية للبيع)

**Status:** **COMPLETE — all 6 waves delivered and verified on `main` (2026-10-18).**
Wave results are recorded in `HANDOFF.md` §Current milestone. The buyer-facing
entry point is `docs/BUYER_PACKAGE.md`; the per-release gate is
`docs/RELEASE_CHECKLIST.md`. Waves below are kept for provenance; re-running one
is safe and deterministic.
**Previously:** authoritative, living
**Date:** 2026-10-18
**Applies to:** any agent or developer preparing this product for sale.

This plan upgrades the repo beyond "functionally complete" (§ Stage 1–7 are
already green) to **"sell-ready"**: a buyer gets a product that runs with `$0`
resources, deploys with one command, is packaged with a complete ownership kit,
and has a documented path for the decisions only a human/buyer can make.

> Read first: `HANDOFF.md` then `docs/architecture/EXECUTION_PLAN.md` (Stage 7
> finishing rules still apply). This plan supersedes nothing — it ADDS Waves
> that finish Stage 7 and add the sales layer.

---

## P0. Operating rules (identical to EXECUTION_PLAN §1)

1. Commit + push after every completed Wave:
   `git add -A && git commit -m "<msg>" && git push origin main` (PAT already
   in remote; never print it).
2. **Verify before DONE** — run that Wave's check command block; all must exit 0.
3. No scope creep: build exactly what a Wave names. New ideas → Deferred (§7).
4. Time box = 2 attempts per item, then write FAIL in `HANDOFF.md`, push, move on.
5. **Never weaken a test** to make it pass.
6. No human-only decisions (store accounts, payment gateway keys, company name,
   logo, pricing, ToS legal text) — those go to §6 "Buyer-only decisions" and
   are documented, never invented.

---

## Wave 0 — Current state gate

Run once; all must pass; record in `HANDOFF.md`.

```bash
cd backend && python -m pytest -q && python -m ruff check app tests && ../scripts/smoke_test.py
cd web && npm run build && npx vitest run && npm run lint
cd mobile && npx tsc --noEmit
```

**Check:** exit 0 everywhere.
If anything fails, STOP and fix before Wave 1.

---

## Wave 1 — One-command deploy (Docker Compose)

**Goal:** a buyer runs the whole product locally or on a VPS with
`docker compose up -d` — backend API + web static + ingestion worker + SQLite
volume. This is the #1 missing sales requirement (review: "no real deployment").

Steps (commit once at the end of the Wave):

1. `deploy/Dockerfile.backend` — base `python:3.13-slim`;
   `pip install .` from a copied `backend/`; CMD
   `uvicorn app.main:app --host 0.0.0.0 --port 8000`.
2. `deploy/Dockerfile.web` — multi-stage: build with `node:24-alpine`
   (`npm ci && npm run build`), serve `dist/` with `nginx:alpine` (Vite SPA →
   nginx config must fall back to `/index.html` for SPA routes).
3. `deploy/docker-compose.yml` —
   - services: `backend` (build Dockerfile.backend, port 8000, env from
     `.env` or defaults, volume `./data:/app/data`, healthcheck `curl /healthz`),
     `worker` (same image, command `python -m app.workers.ingestion`),
     `web` (build Dockerfile.web, ports 80:80, healthcheck on `/`).
   - SQLite at `/app/data/trendcipher.db` (volume `trendcipher-data`).
   - one-line restart policy; no paid services.
4. `deploy/.env.example` — same keys as root `.env.example` + `DATABASE_URL=sqlite:////app/data/trendcipher.db`,
   `CORS_ORIGINS=http://localhost`, `PUBLIC_BASE_URL=http://localhost`.
5. `docs/setup/DEPLOYMENT.md` from EXECUTION_PLAN §3.3 points to `deploy/`.

**Check (all 0):**
```bash
test -f deploy/Dockerfile.backend && test -f deploy/Dockerfile.web \
  && test -f deploy/docker-compose.yml && test -f deploy/.env.example
# + real proof only if Docker is available on the worker:
docker compose -f deploy/docker-compose.yml config -q \
  && curl -fsS http://localhost/healthz
```
If Docker is not available in the environment, the file-existence checks still
run; record "Docker build not executed here — CI/next owner must run
`docker compose up`" as an honest note in DEPLOYMENT.md.

**Commit msg:** `feat(deploy): docker compose one-command stack (backend+web+worker, sqlite volume)`

**Time box:** 3 × 45 min.

---

## Wave 2 — Rebrandable product (config-driven name)

**Goal:** the visible product name/short tagline come from config, not hardcoded
strings, so a buyer rebrands in ~5 minutes without touching code.

1. Add `APP_NAME`-driven display anywhere it is hardcoded:
   - `backend`: `settings.app_name` is already used by FastAPI title + `/healthz`.
   - `web`: replace "TrendCipher" literals in `Landing.tsx`, `Login.tsx`,
     `Register.tsx`, `index.html` `<title>`, and sidebar/nav with
     `import.meta.env.VITE_APP_NAME || 'TrendCipher'`.
   - `web/.env.example`: add `VITE_APP_NAME=TrendCipher`.
   - `mobile`: `app.json` "name"/"slug" — document a `npx expo prebuild` +
     config-plugin/env note in `mobile/README.md`; keep current name as default.
2. `docs/REBRAND.md` — 10-step buyer rebrand guide (name, tagline, colors via
   CSS variables in `web/src/styles/global.css`, package names, logo slot).
3. Web build must still pass with default name (no env) and with a test value.

**Check:** `grep -rn "VITE_APP_NAME" web/src | wc -l` ≥ 1 and
`test -f docs/REBRAND.md` and `cd web && npm run build` exit 0.

**Commit msg:** `feat(web): config-driven app name via VITE_APP_NAME + docs/REBRAND.md`

**Time box:** 2 × 45 min.

---

## Wave 3 — Operator docs + security/license closure

**Goal:** any non-developer can operate, back up, and recover; licenses and
secrets are provably handled. (Moves Stage 7 remaining checklist to complete.)

1. `docs/setup/DEPLOYMENT.md` — full (from Wave 1 + EXECUTION_PLAN §3.3), incl.
   `SECRET_KEY` generation, CORS, reverse proxy, worker process.
2. `docs/setup/BACKUP_RECOVERY.md` — `sqlite3 .backup`, cron example, restore +
   verify, Postgres migration pointer.
3. `docs/setup/SECRET_SCAN.md` — gitleaks-based procedure + one actual run
   recorded with **0 findings** (do not modify code for this).
4. `docs/licenses/{backend,web,mobile}.txt` — generated via
   `pip-licenses` (backend) and `npm ls --omit=dev --all` (web, mobile); plus
   `docs/licenses/README.md` pointing to `DATA_PROVIDERS_AND_LICENSING.md` §11.
5. Wire all files into README "Documentation" list.

**Check:**
```bash
for f in docs/setup/DEPLOYMENT.md docs/setup/BACKUP_RECOVERY.md \
  docs/setup/SECRET_SCAN.md docs/licenses/backend.txt docs/licenses/web.txt \
  docs/licenses/mobile.txt; do test -f "$f" || echo "MISSING $f"; done
```
(empty output = pass) and `grep -q "0 findings" docs/setup/SECRET_SCAN.md`.

**Commit msg:** `docs(ops): deployment/backup/recovery guides, secret scan (0 findings), license inventories`

**Time box:** 3 × 45 min.

---

## Wave 4 — Frontend test coverage bump (small, targeted)

**Goal:** fix the weakest-quality point measured in review (5 web tests vs 136
backend tests) without scope creep. Add **integration-style** tests for the two
highest-risk flows using existing vitest + testing-library, against a mocked
`web/src/lib/api.ts`:

1. `web/src/pages/Dashboard.test.tsx` — renders tickers/sidebar/news slot,
   shows loading → loaded state, renders empty/error state when api throws.
2. `web/src/pages/AuthFlow.test.tsx` — register → login → token stored → logout
   calls api and clears token (drive actual plumbing, no `vi.mock` of the
   request layer unless strictly necessary).
3. Keep existing suites green.

**Check:** `cd web && npx vitest run` exit 0 and test count ≥ 8 total.

**Commit msg:** `test(web): integration tests for dashboard states and auth flow`

**Time box:** 2 × 45 min.

---

## Wave 5 — Buyer ownership package

**Goal:** a single folder/document set that converts a technically competent
buyer into an operating owner in one reading.

1. `docs/BUYER_PACKAGE.md` — executive summary (what it is, what it is NOT),
   features table (web/mobile/backend), architecture at a glance, $0 operating
   cost table (from MASTER_ARCHITECTURE §13), real-data providers & licensing
   summary, compliance/positioning note (**NOT financial advice; no calibrated
   win rates**), and "How to sell it onwards" notes (rebrand → deploy → stores).
2. `docs/SETUP_INSTRUCTIONS.md` — 30-line quickstart (clone, install, run,
   first-user super_admin, open web, run worker).
3. `docs/RELEASE_CHECKLIST.md` — Release-DoD 10 items with evidence pointers;
   mark push-E2E + mobile-store publication as "buyer-owned" with exact blocker
   text (physical device + platform accounts).
4. `docs/SELLER_GUIDE.md` — the 6 sales-product gaps from the review and the
   one-line answer for each (e.g., "push not device-proven — plugin is complete,
   delivery verification requires a $0 Expo dev build + your phone/accounts").

**Check:**
```bash
for f in docs/BUYER_PACKAGE.md docs/SETUP_INSTRUCTIONS.md \
  docs/RELEASE_CHECKLIST.md docs/SELLER_GUIDE.md; do test -f "$f" || echo "MISSING $f"; done
```
(empty output = pass) and each file ≥ 20 lines.

**Commit msg:** `docs(sale): buyer package, quickstart, release checklist, seller guide`

**Time box:** 2 × 45 min.

---

## Wave 6 — Final polish, acceptance, close-out

1. Update `README.md` (badges, status "sell-ready", docs list incl. new files).
2. Update `HANDOFF.md`: checkpoint = final SHA, remaining list =
   buyer-owned items only; mark Stage 7 + sales layer COMPLETE.
3. Update `docs/architecture/IMPLEMENTATION_ROADMAP.md`: check every box
   incl. the new deploy/rebrand/license/sales items; final priority note.
4. Update `AGENTS.md` current-stage pointer to the final state.
5. Final gate — full fresh-clone run (same block as EXECUTION_PLAN §7).

**Check:** git status clean; remote HEAD == local HEAD;
`grep -q "sell-ready" README.md`; all Wave-0 commands green in a fresh clone.

**Commit msg:** `chore(handover): final acceptance, docs sync, roadmap close-out — sell-ready`

**Time box:** 2 × 30 min.

---

## Suggested commit order (one per Wave → 6 pushes)

| # | Wave | Message |
|---|---|---|
| 1 | W1 | `feat(deploy): docker compose one-command stack (backend+web+worker, sqlite volume)` |
| 2 | W2 | `feat(web): config-driven app name via VITE_APP_NAME + docs/REBRAND.md` |
| 3 | W3 | `docs(ops): deployment/backup/recovery guides, secret scan (0 findings), license inventories` |
| 4 | W4 | `test(web): integration tests for dashboard states and auth flow` |
| 5 | W5 | `docs(sale): buyer package, quickstart, release checklist, seller guide` |
| 6 | W6 | `chore(handover): final acceptance, docs sync, roadmap close-out — sell-ready` |

After each push: verify `git ls-remote origin main` == local `git rev-parse HEAD`.

---

## §7 Deferred / Buyer-only decisions (NEVER do these; document instead)

| Item | Owner | Why |
|---|---|---|
| Company/legal name, logo, tagline, colors | Buyer | Brand identity — inventory exists after W2 |
| Public hosting / domain / SSL | Buyer | Money + account needed |
| Real payment gateway (Stripe/Paddle) | Buyer | Business decision + bank account |
| iOS/Android store publication + signing | Buyer | Paid accounts, device, legal |
| Real push E2E on a physical device | Buyer | Physical device + platform accounts |
| Binance/Bybit providers | Buyer choice | Geo-blocked here; ToS redistribution check |
| Postgres migration in production | Buyer | Option; documented |
| vite 5→8 / vitest 2→5 / Expo/RN major upgrades | Buyer | Breaking toolchain bumps |
| AI/ML model for predictions | NOBODY | Contradicts the honest/no-win-rate brand |

## §8 Definition of "Sell-ready DONE" (final gate)

- Deploy: one-command `docker compose up` documented and config-validated.
- Run: all Wave-0 checks green in a fresh clone in the current environment.
- Rebrand: `VITE_APP_NAME` + `docs/REBRAND.md` (5-minute path, code untouched).
- Operate: DEPLOYMENT + BACKUP_RECOVERY + SECRET_SCAN + licenses committed.
- Package: BUYER_PACKAGE + SETUP_INSTRUCTIONS + RELEASE_CHECKLIST + SELLER_GUIDE.
- Close-out: README/HANDOFF/ROADMAP/AGENTS all reflect sell-ready state and the
  only remaining items are buyer-owned.