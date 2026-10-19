# TrendCipher

A professional, explainable cryptocurrency market-intelligence platform that
combines **news intelligence** and **candlestick/technical analysis** into a
single deterministic analysis engine.

> **Working name — configurable.** "TrendCipher" is a provisional name. Product
> branding is kept configurable for the buyer.

## What makes it different

- **Explainable:** every analytical scenario records its rule version, the exact
  inputs, and its reasoning.
- **Deterministic:** identical inputs always produce identical outputs — no
  black box.
- **Honest:** news is treated as evidence, not fact; headlines never imply price
  predictions; mock/demo data is always labeled.
- **$0 development:** all default data sources and libraries are free; no paid
  subscription is required to build, test, or demonstrate the product.
- **Transferable:** a complete source-code package for a buyer who wants to
  rebrand, customize, or operate it as a SaaS product.

## Repository layout

```
backend/   FastAPI application (auth, ingestion, analysis, admin)
web/       React + Vite + TypeScript client (marketing + product)
mobile/    Expo / React Native client (Android + iOS)
docs/      Architecture, setup, operator, and handover documentation
scripts/   Dev/ops helper scripts
```

## Documentation

- **Master architecture:** `docs/architecture/MASTER_ARCHITECTURE.md`
- **Data providers & licensing:** `docs/architecture/DATA_PROVIDERS_AND_LICENSING.md`
- **Analytical engine:** `docs/architecture/ANALYTICAL_ENGINE.md`
- **Security & privacy:** `docs/architecture/SECURITY_AND_PRIVACY.md`
- **Roadmap:** `docs/architecture/IMPLEMENTATION_ROADMAP.md`
- **Decision records:** `docs/architecture/ARCHITECTURE_DECISIONS.md`
- **Definition of done:** `docs/architecture/DEFINITION_OF_DONE.md`

### Run & operate (buyer)

- **Deploy (one command, Docker Compose):** `docs/setup/DEPLOYMENT.md`
- **Rebrand in 5 minutes:** `docs/REBRAND.md`
- **Backup & restore:** `docs/setup/BACKUP_RECOVERY.md`
- **Secret scan procedure:** `docs/setup/SECRET_SCAN.md`
- **Third-party licenses:** `docs/licenses/LICENSE_SUMMARY.md` (+ inventories in `docs/licenses/`)
- **Handoff / progress log:** `HANDOFF.md`

## Status

See `HANDOFF.md` for the current milestone and verified state.

> This document and the repository were created/updated by an AI agent
> (OpenHands) on behalf of the repository owner.