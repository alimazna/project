# TrendCipher — Handoff and Progress Log

This is the **living** handover document. It records the verified state of the
repository, the latest commit, what works, what is pending, testing status, and
any blockers — so a new developer or buyer can take over without a phone call.

---

## Current milestone

**Backend foundation (Stage 1) and real-data pipeline (Stage 2): COMPLETE and pushed**

- FastAPI backend with auth, provider adapters, ingestion worker, and read API.
- Live dashboard wired to real Kraken + CoinTelegraph/CoinDesk data.

### Latest verified commit (checkpoint)

| Key | Value |
|---|---|
| Commit | `feat: Stage 2 data pipeline — market/news providers, ingestion, market API, real-data dashboard` |
| Branch | `main` |
| Remote | `https://github.com/alimazna/project` |
| Verified | `git push` succeeded; remote `origin/main` shows the commit |

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

- **Stage 3 — Analytical engine** (indicators, news classifier, decision matrix,
  scenario state machine, backtest): the next milestone.
- Stage 4 — functional web product beyond the dashboard (charts, watchlist,
  scanner, scenario view).
- Stage 5 — SaaS admin (RBAC admin UI, quotas, billing abstraction).
- Stage 6 — mobile app + push.
- Stage 7 — validation & handover.

## Testing status

- Backend: `29 passed` (pytest), `ruff check` clean.
- Web: `2 passed` (vitest); ESLint 9 flat config clean; production build passes.
- Next: engine unit tests (determinism, no-lookahead, dedup, non-actionable).

---

## Next milestones (in progress)

1. ~~**Stage 1 — Repository & foundation**~~ — DONE (scaffold backend/web, auth, tests).
2. ~~**Stage 2 — Real data pipeline**~~ — DONE (Kraken/OKX/RSS → DB → read API; live dashboard).
3. **Stage 3 — Analytical engine** — IN PROGRESS (indicators, news classifier, decision matrix, scenarios, backtest).
4. **Stage 4 — Web product** — STARTED (dashboard live; charts, watchlist, scanner, scenario view pending).
5. **Stage 5 — SaaS + Super Admin.**
6. **Stage 6 — Mobile + push.**
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