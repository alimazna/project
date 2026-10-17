# TrendCipher — Implementation Roadmap

**Status:** Baseline
**Date:** 2026-10-17

Phases are sequential where dependencies require it; each has concrete acceptance
criteria. Progress is tracked in `HANDOFF.md` with commit SHAs.

---

## Stage 1 — Repository and foundation

**Goal:** Initialize monorepo, CI, tooling, and a running dev slice.

- [ ] Monorepo layout: `backend/`, `web/`, `mobile/`, `docs/`, `scripts/`.
- [ ] Backend: FastAPI app skeleton, settings, SQLite (WAL), Alembic migrations
      (or SQLAlchemy create_all bootstrap + migration path).
- [ ] Tests: pytest + fixtures; lint (ruff).
- [ ] Web: Vite + React + TS scaffold; ESLint + Prettier.
- [ ] Mobile: Expo (TypeScript) template commit (runs in dev).
- [ ] CI: GitHub Actions — backend tests, ruff, web build/lint, license report.
- [ ] `.env.example`, README base, `HANDOFF.md`.

**Acceptance:** `python -m pytest` passes on backend; `npm run build` passes on
web; CI green where runners available.

## Stage 2 — Real data pipeline

**Goal:** Real provider data flows into the backend and API.

- [ ] Market provider abstraction + Kraken adapter (OHLC, tickers, symbols).
- [ ] OKX fallback adapter.
- [ ] Ingestion worker (periodic loop) with health/state table.
- [ ] Candle/ticker/error/staleness handling; backfill pagination.
- [ ] News provider abstraction + CoinTelegraph RSS adapter (+CoinDesk redirect
      handling).
- [ ] News normalization, dedup, timestamps; store to DB.
- [ ] Tests with recorded fixtures + live smoke test (labeled).

**Acceptance:** CLI or worker run stores real Kraken candles + CoinTelegraph news
with `is_live: true` provenance; stale/timeout paths return explicit states.

## Stage 3 — Analytical engine

**Goal:** Deterministic, explainable scenarios from real data.

- [ ] Indicators: EMA, RSI, ATR, SMA, volume z, structure/S-R pivots.
- [ ] News classifier: sentiment lexicon, asset mapping, relevance score.
- [ ] Unified decision matrix + scenario state machine.
- [ ] Rule-version storage + traceable evidence JSON.
- [ ] Leakage-guard backtest runner + repro test.
- [ ] Unit tests for determinism, no-lookahead, dedup, non-actionable states.

**Acceptance:** engine unit tests pass; scenario JSON has full evidence &
rule_version; backtest reproduces identical output on same snapshot.

## Stage 4 — Functional web product

**Goal:** Working, integrated, professional web client.

- [ ] Design system (tokens, components, states, responsive).
- [ ] Marketing site (landing, methodology, pricing, legal placeholders).
- [ ] App shell: dashboard, watchlist, symbol search, asset detail, charts
      (lightweight-charts), scanner, news feed+filter, news&price view.
- [ ] Scenario timeline view (historical + current), levels on chart.
- [ ] Alerts CRUD UI, notification preferences, account settings.
- [ ] Loading/empty/error/stale states wired to backend status.

**Acceptance:** all major views call real backend endpoints; every button
performs its function; error states reflect real API responses.

## Stage 5 — SaaS and Super Admin

**Goal:** Role-based SaaS admin with database-driven plans.

- [ ] Auth register/login/logout/me + refresh; rate limiting.
- [ ] RBAC decorators; admin user management.
- [ ] Plans/features CRUD + pricing page rendering from API.
- [ ] Quota enforcement server-side.
- [ ] Admin dashboard: users, plans, health, providers, logs, settings, audit.
- [ ] Billing provider abstraction + labeled demo mode.

**Acceptance:** super_admin can create plan and see it on public pricing page;
quotas enforced at API level; auth tests pass.

## Stage 6 — Android/iOS application

**Goal:** Shared Expo client consuming the same API.

- [ ] Expo app: auth, dashboard, watchlist, asset detail + charts (lightweight
      charts web-based or react-native equivalent), news list, scenario view.
- [ ] Alerts + notification preference screens.
- [ ] Device token registration endpoint integration.
- [ ] Push provider abstraction (Expo/log) + delivery attempts.
- [ ] Build instructions (EAS/local) + honest verification notes.

**Acceptance:** app launches in Expo dev with backend URL; push flow verified as
far as possible without physical device; docs cover credentials.

## Stage 7 — Validation and handover

**Goal:** Verify, document, package for buyer.

- [ ] E2E smoke tests (API-driven + web).
- [ ] Fresh-install verification from README.
- [ ] Security checks (audit, dependency scan, secret scan).
- [ ] Deployment/backup/recovery docs.
- [ ] License inventory + data-provider terms summary.
- [ ] Buyer handover package & release checklist.
- [ ] Final `HANDOFF.md` with full verified state.

**Acceptance:** a new owner can install and run the product with only free
resources and public data, following the documentation, without contacting us.

---

## Prioritization policy

If time becomes constrained, the priority order is:

1. Backend + data pipeline + engine (the product's core value).
2. Web client integration (the visible product).
3. SaaS/Admin (commercial capability).
4. Mobile app (shared code, lower fidelity acceptable).
5. Push notification end-to-end verification (blocked by device requirement).

No phase is marked complete without its acceptance criteria being met or a
documented exception in `HANDOFF.md`.