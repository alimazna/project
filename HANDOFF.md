# TrendCipher — Handoff and Progress Log

This is the **living** handover document. It records the verified state of the
repository, the latest commit, what works, what is pending, testing status, and
any blockers — so a new developer or buyer can take over without a phone call.

---

## Current milestone

**Stages 1–5: COMPLETE and pushed** (foundation, data pipeline, analytical
engine, web product, SaaS+admin system overview).
**Stage 6 (Mobile + push): DONE** (except physical-device push delivery) —
backend push abstraction pushed (`716bd71`); Expo app pushed (`b1a6e16`); mobile
dashboard now includes the **news list** (`9b7309d`, roadmap checklist item).
**Stage 7 (Validation & handover): STARTED** — API-driven E2E smoke test added
(`scripts/smoke_test.py`, 36 steps green) and web news feed+filter completed
(`5b5d910`).

- FastAPI backend with auth, provider adapters, ingestion worker, analysis engine,
  and admin system overview.
- Web product: dashboard (tickers + charts + scenario card + **news feed with
  source filter**), asset detail + charts, scanner, scenarios, watchlist,
  alerts, account, plans, admin panel.
- Mobile (Expo/React Native): auth (login/register), dashboard (**tickers +
  market news list**), watchlist, scenarios, alerts, account with push
  registration, asset detail (candles + analysis run / watchlist add),
  analysis detail. Push: expo-notifications + provider abstraction (log default).
- CI workflow added: `.github/workflows/ci.yml`.

### Latest verified commit (checkpoint)

| Key | Value |
|---|---|
| Last commit | `697e2a3` — `feat(scripts): API-driven E2E smoke test — 36 steps across the full product journey (Stage 7)` |
| Branch | `main` |
| Remote | `https://github.com/alimazna/project` |
| Verified | `git ls-remote origin main` == local HEAD == `697e2a39ae9fc5bf690ae5e917206bc5cd548582` (confirmed after push) |

> **History note (reset):** the remote `main` was force-pushed/re-written at
> some point during Stage 6 delivery. HANDOFF previously documented commit
> `021bf30` (a single squashed Stage 1–5 commit, `e8dd9b3`) and then advanced to
> `716bd71` (`feat(push): provider abstraction with log/expo adapters + alert
> push dispatch — Stage 6`). The current remote HEAD is `697e2a3`; any
> references to `021bf30` are stale and should be ignored.

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
  accounts (documented under Blockers); the codebase plumbing is in place.
- **Stage 7 — validation & handover** (in progress: E2E smoke test done; still
  pending fresh-install verification, security audit follow-through, license
  inventory publish, deployment/backup docs, buyer package).

## Testing status

- Backend: `136 passed` (pytest), `ruff check` clean.
- Web: `5 passed` (vitest); ESLint 9 flat config clean; production build passes.
- **E2E smoke test: `scripts/smoke_test.py`** — 36 steps green (deterministic,
  isolated SQLite): public endpoints, auth (register→login→me→refresh),
  market data, news+source-filter, analysis run/persist/detail/backtest,
  watchlists, alerts CRUD+evaluate, notification prefs, device registration,
  subscription, admin overview/users/plans, and unauthorized-access rejection.
- CI workflow: **green on GitHub Actions** — confirmed 2026-10-18 for commits
  `716bd71`, `b1a6e16`, `83a81bc`, `4e88ab3`, and `9b7309d` (backend tests+lint,
  web build+lint+tests, license report all pass).
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

## Next milestones (in progress)

1. ~~**Stage 1 — Repository & foundation**~~ — DONE (scaffold backend/web, auth, tests, CI workflow added).
2. ~~**Stage 2 — Real data pipeline**~~ — DONE (Kraken/OKX/RSS → DB → read API; live dashboard).
3. ~~**Stage 3 — Analytical engine**~~ — DONE (indicators, news classifier, decision matrix, backtest, analysis API, dashboard scenario card).
4. ~~**Stage 4 — Web product**~~ — MOSTLY DONE (dashboard incl. scenario card, signal scanner + backtest stats, scenario history, asset detail + charts, watchlist, alerts, account, admin; final acceptance pass pending).
5. ~~**Stage 5 — SaaS + Super Admin**~~ — DONE (RBAC, plans CRUD, quotas, billing abstraction, admin user management, system overview).
6. ~~**Stage 6 — Mobile + push.**~~ — DONE except physical-device push delivery:
   backend push abstraction (`716bd71`), Expo app (`b1a6e16`) with dashboard news
   list added (`9b7309d`). Remaining (non-blocking): real push E2E on a physical
   device + final acceptance pass.
7. **Stage 7 — Validation & handover.** — IN PROGRESS — API-driven E2E smoke
   test done (`scripts/smoke_test.py`, 36 green); next: fresh-install
   verification from README, security/dependency audit follow-through, license
   inventory publish, deployment/backup docs, buyer package, final HANDOFF.

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