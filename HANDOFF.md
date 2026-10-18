# TrendCipher — Handoff and Progress Log

This is the **living** handover document. It records the verified state of the
repository, the latest commit, what works, what is pending, testing status, and
any blockers — so a new developer or buyer can take over without a phone call.

---

## Current milestone

**Stages 1–5: COMPLETE and pushed** (foundation, data pipeline, analytical
engine, web product, SaaS+admin system overview).

- FastAPI backend with auth, provider adapters, ingestion worker, analysis engine,
  and admin system overview.
- Web product: dashboard, asset detail + charts, scanner, scenarios, watchlist,
  alerts, account, plans, admin panel.
- CI workflow added: `.github/workflows/ci.yml`.

### Latest verified commit (checkpoint)

| Key | Value |
|---|---|
| Commit | `feat(admin): system overview — counts, provider health, billing (Stage 5f)` |
| Branch | `main` |
| Remote | `https://github.com/alimazna/project` |
| Verified | `git push` succeeded; remote `origin/main` shows the commit (`021bf30`) |

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

- **CI verified green on GitHub** — workflow added and locally green; awaiting
  first GitHub Actions run after next push.
- **Stage 6 — mobile app (Expo) + push delivery.**
- **Stage 7 — validation & handover** (E2E smoke, fresh-install verification,
  security audit, license inventory publish, buyer package).

## Testing status

- Backend: `128 passed` (pytest), `ruff check` clean.
- Web: `5 passed` (vitest); ESLint 9 flat config clean; production build passes.
- CI workflow: locally green (backend pytest+ruff, web build+eslint+vitest,
  license report jobs); first GitHub Actions run pending after push.
- Engine: indicators (EMA/RSI/ATR/vol/S-R), news classifier, decision-matrix
  scenario builder, leakage-guarded walk-forward backtest, analysis API
  (POST /analysis/run, GET /scenarios, GET /analysis/backtest) — deterministic.
- Dashboard: "Scenario — explainable" card (direction, alignment, entry/stop/
  targets, per-signal reasons) wired to POST /analysis/run with Re-run button.
- Web pages: Signal Scanner (tickers × last scenario + walk-forward backtest
  stats per symbol) and Scenario history (persisted scenarios with filter).

---

## Next milestones (in progress)

1. ~~**Stage 1 — Repository & foundation**~~ — DONE (scaffold backend/web, auth, tests, CI workflow added).
2. ~~**Stage 2 — Real data pipeline**~~ — DONE (Kraken/OKX/RSS → DB → read API; live dashboard).
3. ~~**Stage 3 — Analytical engine**~~ — DONE (indicators, news classifier, decision matrix, backtest, analysis API, dashboard scenario card).
4. ~~**Stage 4 — Web product**~~ — MOSTLY DONE (dashboard incl. scenario card, signal scanner + backtest stats, scenario history, asset detail + charts, watchlist, alerts, account, admin; final acceptance pass pending).
5. ~~**Stage 5 — SaaS + Super Admin**~~ — DONE (RBAC, plans CRUD, quotas, billing abstraction, admin user management, system overview).
6. **Stage 6 — Mobile + push.** — NEXT
7. **Stage 7 — Validation & handover.**

## Blockers / external dependencies

- Binance/Bybit geo-blocked from this dev environment — not required for the
  build (Kraken/OKX used).
- Real push notification delivery requires a physical device + platform
  accounts — documented; not blocking the codebase.
- No paid account is required to develop, test, or demonstrate the product at $0.

---

## How to update this file

After every milestone:

1. Run tests; record pass/fail.
2. Record the commit SHA and whether the push was verified.
3. Update "What works", "What is pending", and blockers honestly.