# TrendCipher — Architecture Decision Records

**Date:** 2026-10-17

This file records significant decisions with rationale and alternatives
considered. Format follows a lightweight ADR style.

---

## ADR-001: Monorepo for all product components

**Decision:** One GitHub repository containing `backend/`, `web/`, `mobile/`,
`docs/`, `scripts/`, `.github/`.

**Rationale:** Single transferable artifact for the buyer; shared API contract is
easier to keep consistent; single CI surface. Cost: unrelated changes share a
repo (acceptable for a small team/solo product).

**Alternatives:** Separate repos per component — rejected (harder handover).

---

## ADR-002: Backend = one FastAPI service

**Decision:** A single Python FastAPI process providing REST API + background
ingestion workers (asyncio tasks or APScheduler)-style loops.

**Rationale:** FastAPI is async, typed (Pydantic), testable, and runs on SQLite
for $0. One process keeps deployment trivial and rate-limit/queue logic
centralized at this product's scale.

**Alternatives:** Node/NestJS backend (rejected: Python better for numeric
analysis); separate worker pods (rejected: unnecessary infra for the target
scale).

---

## ADR-003: Default database = SQLite (WAL), PostgreSQL-ready

**Decision:** SQLite in WAL mode in dev/single-node; all models via SQLAlchemy so
PostgreSQL is a configuration change (plus a migration script) for buyers.

**Rationale:** $0, zero-ops, ACID, sufficient for single-machine SaaS demo.
PostgreSQL path keeps future scaling honest.

**Alternatives:** PostgreSQL from day one (rejected: requires a server/dependency
for no benefit at dev scale); MongoDB (rejected: relational integrity preferred
for entitlements/audits).

---

## ADR-004: Market-data provider abstraction with Kraken default

**Decision:** `MarketDataProvider` protocol; default adapter **Kraken** public
REST, fallback **OKX**.

**Rationale:** Verified reachable from this environment on 2026-10-17; public
endpoints work without keys. Binance/Bybit are geo-blocked from this dev
environment and Binance's ToS restrict commercial data redistribution, so they
are not the default.

**Alternatives:** Binance (blocked + restrictive), Bybit (blocked), Coinbase
(works but narrower instrument metadata and heavier rate limiting observed),
KuCoin (works but rate limits tighter). Kraken + OKX chosen for balance of symbol
coverage, historical data, and reachability.

---

## ADR-005: News via RSS with deterministic classification

**Decision:** News ingestion from public RSS feeds (CoinTelegraph default,
CoinDesk fallback) with lexicographic classification, no paid NLP/LLM dependency.

**Rationale:** Satisfies the requirement "Do not require a paid AI model" while
keeping classification transparent and testable. Optional NLP can be added behind
a `NewsClassifier` interface later only if it provides measurable value.

---

## ADR-006: Deterministic analysis engine with strict no-lookahead

**Decision:** Pure, deterministic engine; closed candles only; rule-versioned
outputs; explicit non-actionable states.

**Rationale:** Reproducible, auditable, testable — the core commercial value of
an "explainable" analysis product. Prevents the look-ahead-bias class of defects
before it can happen.

---

## ADR-007: TradingView Lightweight Charts (Apache-2.0) for web charts

**Decision:** Use `lightweight-charts` on the web client.

**Rationale:** Free, open-source (Apache-2.0), small (35 KB), maintained,
candlestick-ready, mobile-friendly. Attribution requirement honored.

**Alternatives:** TradingView Advanced Charts (proprietary license — rejected);
Chart.js (rejected: weaker financial-chart interactions); ECharts (rejected:
heavier; possible future option).

---

## ADR-008: React + Vite + TypeScript for web client

**Decision:** React 18+ with Vite bundler and TypeScript.

**Rationale:** Fast dev/build, strong ecosystem, TS brings type safety across the
API contract, and it pairs with the design system requirement without server-side
rendering complexity at this stage.

**Alternatives:** Next.js (rejected: SSR complexity not needed for an
authenticated app; SEO of the marketing pages is handled by a static/public
route instead); Vue/Svelte (viable but React maximizes buyer-pool familiarity).

---

## ADR-009: Expo (React Native) for Android/iOS

**Decision:** Shared mobile codebase using Expo SDK (TypeScript).

**Rationale:** One codebase for both platforms; free local dev; Expo Push
provides a zero-cost notification path; documented SDK 53+ requirement for dev
builds. Store publication remains out of scope (owner decision: web-first,
Expo Go / side-loaded APK — see `docs/setup/EXPO_GO_HOWTO.md`).

---

## ADR-010: Database-driven plans/pricing/entitlements

**Decision:** Plans, prices, features, quotas stored in DB; exposed via API;
Super Admin edits them.

**Rationale:** Requirement: "Plan names, displayed prices, features, and limits
must be database-driven ... Do not hardcode them." Also gives the buyer a SaaS
capability with no code changes.

---

## ADR-011: Billing-provider abstraction + demo mode only

**Decision:** `PaymentProvider` protocol; demo mode explicitly labeled; no real
gateway in the base build.

**Rationale:** No paid services at $0; buyer configures their own gateway later.
Keeps the domain model (subscriptions/payments/invoices) clean and forward-fitting.

---

## ADR-012: Push notifications via abstraction, default log/expo

**Decision:** `PushProvider` protocol with `LogOnlyPushProvider` (default in dev)
and `ExpoPushProvider` (device-facing).

**Rationale:** Honest verification: real push needs a physical device and
platform credentials which are outside $0 scope. The code path, tables, and
setup docs are delivered; provider is swappable.

---

## ADR-013: No secrets in repos; `.env.example` placeholders

**Decision:** All credentials via environment variables; `.env.example` has only
placeholder values; CI includes secret scanning.

**Rationale:** Security requirement and buyer-transferability (original owner's
credentials must not be embedded).

---

## ADR-014: Monolithic-repo CI in GitHub Actions

**Decision:** Single workflow running backend tests, lint, typecheck, web build,
and license report.

**Rationale:** Free for public repos, one place to review all gates, easy for a
buyer to take over.

---

## Deferred / open decisions

- **NLP classifier upgrade path** — only if it improves value and stays free.
- **Multiple deployments (Docker compose vs bare process)** — both documented;
  no paid infra assumed.
- **Any paid SaaS features** — explicitly out of the $0 build; buyer configures.