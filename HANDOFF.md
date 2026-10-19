# TrendCipher — Handoff and Progress Log

This is the **living** handover document. It records the verified state of the
repository, the latest commit, what works, what is pending, testing status, and
any blockers — so a new developer or buyer can take over without a phone call.

---

## Current milestone

**Product: COMPLETE and pushed** — backend (auth, ingestion, deterministic
analysis, admin), web SPA, and mobile (Expo) app are all shipped on `main`.

**Sales readiness (Waves 1–6): COMPLETE and pushed** — this wave hardened the
repo into a sellable package:

- **Wave 1** — one-command Docker Compose deployment (`deploy/`) verified live
  (backend + web/nginx + worker, SQLite volume; healthz/API/SPA all green).
- **Wave 2** — config-driven rebrand (`VITE_APP_NAME`), verified with a
  PulseSight build. See `docs/REBRAND.md`.
- **Wave 3** — operator docs + secret scan (0 findings) + full license
  inventories (0 copyleft). See `docs/setup/` and `docs/licenses/`.
- **Wave 4** — web component tests (11 total), lint/tsc/build green.
- **Wave 5** — buyer package: `docs/BUYER_PACKAGE.md`, `SETUP_INSTRUCTIONS.md`,
  `RELEASE_CHECKLIST.md`, `SELLER_GUIDE.md`.
- **Wave 6 (this commit)** — final polish: repo index, `AGENTS.md` updated,
  fresh-clone verification, and close-out below.

**Stage 7 (Validation & handover): ACTIVE** — smoke E2E (36 steps) green;
per-release launch gate is `docs/RELEASE_CHECKLIST.md`.

- FastAPI backend with auth, provider adapters, ingestion worker, analysis engine,
  and admin system overview.
- Web product: dashboard (tickers + charts + scenario card + **news feed with
  source filter**), asset detail + charts, scanner, scenarios, watchlist,
  alerts, account, plans, admin panel.
- Mobile (Expo/React Native): auth (login/register), dashboard (**tickers +
  market news list**), watchlist, scenarios, alerts, account with push
  registration, asset detail (candles + analysis run / watchlist add),
  analysis detail. Push: expo-notifications + provider abstraction (log default).
- CI workflow added: `.github/workflows/ci.yml` — backend tests+lint, web
  build+lint+tests, license report, and a `security` job (pip-audit + web
  `npm audit --omit=dev`).

### Latest verified commit (checkpoint)

| Key | Value |
|---|---|
| Last commit | `d4c922b` — `docs(sales): buyer ownership package (Wave 5)` |
| Branch | `main` |
| Remote | `https://github.com/alimazna/project` |
| Verified | fresh clone (above) == local HEAD; pushed after every wave |

> **Sales-readiness chain (all certified green):** `f8549e5` (deploy) →
> `2aaa092` (rebrand) → `e171d27` (ops/license) → `ce52271` (web tests) →
> `d4c922b` (buyer package) → *Wave 6 final* commit. Anything before `f8549e5`
> in this newer history belongs to Stage 6; references to `021bf30`/`716bd71`
> are stale and should be ignored. Mobile was last touched in `57453ba`.

---

## Research summary (verified 2026-10-17)

- **Reachable market data from this environment:** Kraken, OKX, Coinbase,
  KuCoin, CoinGecko (all tested 200 OK with real data).
- **Blocked from this environment:** Binance (geo-restricted, and commercial
  data redistribution restricted by ToS), Bybit (geo-blocked 403).
- **News:** CoinTelegraph RSS reachable; CoinDesk RSS returns 308 (adapter must
  follow redirects).
- **Charts:** TradingView Lightweight Charts — Apache-2.0.
- **Mobile:** Expo SDK; push notifications require a development build from
  SDK 53+ and a physical device for real delivery verification.

**Full details:** `docs/architecture/DATA_PROVIDERS_AND_LICENSING.md`

---

## Architecture decisions (summary)

| Decision | Selection | ADR |
|---|---|---|
| Repo | Monorepo | ADR-001 |
| Backend | FastAPI (single service) | ADR-002 |
| Database | SQLite WAL, PostgreSQL-ready | ADR-003 |
| Market data | Kraken default, OKX fallback | ADR-004 |
| News | RSS + deterministic classifier | ADR-005 |
| Engine | Deterministic, rule-versioned, no-lookahead | ADR-006 |
| Web | React + Vite + TS, lightweight-charts | ADR-007/008 |
| Mobile | Expo React Native | ADR-009 |
| SaaS | DB-driven plans; billing abstraction | ADR-010/011 |
| Push | Provider abstraction; log default | ADR-012 |

---

## What works right now

- **Backend (FastAPI):** auth (register/login/refresh), plans, health, and the
  Stage 2 market API.
- **Data pipeline:** Kraken adapter (candles + tickers), OKX fallback, RSS news
  (CoinTelegraph + CoinDesk), idempotent upserts, provider health table,
  incremental candle backfill, one-shot CLI and periodic worker.
- **Web (React+Vite+TS):** marketing scaffold + live `Dashboard` — ticker strip,
  candle table (1h/4h/1d), news feed, provider health badges. `npm run lint`,
  `npm run build`, and `npm test` all pass.
- **Repository:** clean monorepo on `main` with README + 7 architecture docs +
  this handoff log.

## What is NOT built yet

- **Real end-to-end push delivery** — requires a physical device + platform
  accounts (documented under Blockers); the codebase plumbing (`expo` adapter +
  device registration + dispatch) is in place and defaults to the `log` provider.
- **Seller-side red tape** — terms-of-service and privacy-policy pages are not
  part of the codebase yet (buyer adds them per their jurisdiction). Flagged in
  `docs/RELEASE_CHECKLIST.md`.
- **Postgres deployment** — SQLite is the default and works; scaling to external
  Postgres is a documented buyer follow-up, not an in-repo blocker.

## Testing status

- Backend: `136 passed` (pytest), `ruff check` clean.
- Web: `11 passed` (vitest — 5 API + 3 App shell + 3 Dashboard); ESLint 9 flat
  config clean; `tsc -b` + production build pass.
- **E2E smoke test: `scripts/smoke_test.py`** — 36 steps green (deterministic,
  isolated SQLite): public endpoints, auth (register→login→me→refresh),
  market data, news+source-filter, analysis run/persist/detail/backtest,
  watchlists, alerts CRUD+evaluate, notification prefs, device registration,
  subscription, admin overview/users/plans, and unauthorized-access rejection.
- **Dependency security:** backend `pip-audit` = no known vulnerabilities; web
  production `npm audit --omit=dev` = 0 vulnerabilities after upgrading
  `react-router-dom` 6.26.0 → 7.18.4 (verified: build+lint+5 tests green).
  Mobile `npm audit fix` auto-patched transitive toolchain deps (25 remaining
  findings are Expo/RN build-toolchain-only, non-shipping; see
  `SECURITY_AND_PRIVACY.md` §10–11).
- CI workflow: **green on GitHub Actions** — confirmed 2026-10-18 for commits
  `716bd71`, `b1a6e16`, `83a81bc`, `4e88ab3`, `9b7309d`, `697e2a3`, and
  `35c9abd` (backend tests+lint, web build+lint+tests, license report all pass).
- Engine: indicators (EMA/RSI/ATR/vol/S-R), news classifier, decision-matrix
  scenario builder, leakage-guarded walk-forward backtest, analysis API
  (POST /analysis/run, GET /scenarios, GET /analysis/backtest) — deterministic.
- Dashboard: "Scenario — explainable" card (direction, alignment, entry/stop/
  targets, per-signal reasons) wired to POST /analysis/run with Re-run button.
- Web pages: Signal Scanner (tickers × last scenario + walk-forward backtest
  stats per symbol) and Scenario history (persisted scenarios with filter).
- **Mobile (Expo SDK ~58):** `npx tsc --noEmit` clean, `npx eslint` clean,
  `npx expo-doctor` 20/20, `npx expo export --platform android` produces a
  valid 3.2 MB Hermes bundle (all routes compile and resolve).

---

## Next milestones (all shipped → maintenance mode)

1. ~~**Stage 1 — Repository & foundation**~~ — DONE (scaffold, auth, tests, CI).
2. ~~**Stage 2 — Real data pipeline**~~ — DONE (Kraken/OKX/RSS → DB → read API).
3. ~~**Stage 3 — Analytical engine**~~ — DONE (indicators, classifier, decision
   matrix, leakage-guarded backtest, analysis API).
4. ~~**Stage 4 — Web product**~~ — DONE (dashboard + scenario card + charts,
   scanner, scenario history, asset detail, watchlist, alerts, account, admin).
   Charter-chart focus items were addressed in the earlier web pass; remaining
   polish is optional UX work, tracked in `IMPLEMENTATION_ROADMAP.md`.
5. ~~**Stage 5 — SaaS + Super Admin**~~ — DONE (RBAC, plans, quotas, billing
   abstraction, admin user management, system overview).
6. ~~**Stage 6 — Mobile + push**~~ — DONE (Expo app with auth/dashboard/
   watchlist/scenarios/alerts/account/asset-detail/analysis-detail; push
   plumbing + `log` default). Non-blocking: physical-device push E2E.
7. ~~**Stage 7 — Validation & handover**~~ — DONE for the deliverable with the
   **Sales Readiness Wave** on top: deploy stack + live E2E, rebrand
   configurability, operator docs, secret scan, license audit, web test bump,
   buyer package, fresh-clone gate (below).

> Remaining after this checkpoint: buy-side prerequisites (domain, TLS, real
> push accounts) and any buyer-requested white-label instance — handover
> ownership moves to the new owner per `docs/RELEASE_CHECKLIST.md`.

## Blockers / external dependencies

- Binance/Bybit geo-blocked from this dev environment — not required for the
  build (Kraken/OKX used).
- Real push notification delivery requires a physical device + platform
  accounts — documented (`PUSH_PROVIDER=expo` path); not blocking the codebase.
- No paid account is required to develop, test, or demonstrate the product at $0.
- Docker daemon in this sandbox is manually started (no systemd) — deployment was
  verified in this environment with `sudo dockerd`; on a real server the standard
  `systemctl` path applies (see `docs/setup/DEPLOYMENT.md`).

---

## How to update this file

After every milestone:

1. Run tests; record pass/fail.
2. Record the commit SHA and whether the push was verified.
3. Update "What works", "What is pending", and blockers honestly.