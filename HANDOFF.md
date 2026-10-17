# TrendCipher — Handoff and Progress Log

This is the **living** handover document. It records the verified state of the
repository, the latest commit, what works, what is pending, testing status, and
any blockers — so a new developer or buyer can take over without a phone call.

---

## Current milestone

**Phase Zero (research) + Phase One (architecture checkpoint): COMPLETE**

- Research verified which free data providers are reachable and commercially
  sensible.
- Architecture document set committed and pushed to GitHub.

### Latest verified commit (checkpoint)

| Key | Value |
|---|---|
| Commit | `docs: add researched product architecture and implementation roadmap` |
| Branch | `main` |
| Remote | `git@github.com:alimazna/project.git` / `https://github.com/alimazna/project` |
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

- **Repository:** clean monorepo baseline on `main` with README + `docs/`.
- **Architecture documentation:** 7 documents in `docs/architecture/`.
- **Handover doc:** this file.

## What is NOT built yet

- Backend code, database, data pipeline, engine, web app, mobile app. These are
  the explicit next stages (see `docs/architecture/IMPLEMENTATION_ROADMAP.md`).

## Testing status

- No application code exists yet; no tests run beyond `git` itself.

---

## Next milestones (in progress)

1. **Stage 1 — Repository & foundation:** scaffold backend/web/mobile, CI, env
   templates.
2. **Stage 2 — Real data pipeline:** Kraken candles + CoinTelegraph news.
3. **Stage 3 — Analytical engine.**
4. **Stage 4 — Web product.**
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