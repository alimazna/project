# TrendCipher — Definition of Done

**Status:** Baseline
**Date:** 2026-10-17

This is the checklist a feature/milestone/phase must satisfy before it may be
marked complete in the roadmap or reported as done in `HANDOFF.md`.

---

## Per-feature DoD

1. **Implemented:** the feature exists and is wired to the backend (no
   decorative controls).
2. **Tested:** relevant automated tests exist and pass; anything untestable here
   is recorded with the exact reason.
3. **Documented:** its area of the architecture docs, README, or HANDOFF
   reflects the implementation.
4. **Committed & pushed:** a meaningful commit exists on the connected GitHub
   repository, and the remote operation was verified.
5. **No secrets:** credentials are not in source, bundles, logs, or history.

## Cross-cutting DoD

- The frontend (web and mobile) consumes the backend API contract — no direct
  exchange API calls for authoritative results.
- Missing, stale, or failed data produce explicit UI/API states.
- Analysis results are deterministic, rule-versioned, and traceable.
- Nothing is represented as a calibrated probability or guaranteed profit.
- Mocked/demo data is explicitly labeled and never presented as live.
- Admin/plan/pricing changes are enforced server-side.
- The product runs with $0 resources and no hidden dependency on the original
  developer's accounts.

## Data-integrity DoD

- Closed candles only enter analysis; no future data in indicators.
- Repeated processing does not duplicate news or signals.
- News retains original publication timestamps, source URLs, and retrieval time.
- Provider outage → explicit stale/unavailable state, not silent stale reuse.

## Handover DoD

- A new owner can install from scratch following `README.md` + `docs/setup`
  using only free resources.
- `.env.example` provides every configuration key as a placeholder.
- Mobile build instructions and honest verification status are provided.
- Dependency/license/data-provider inventory is committed.
- `HANDOFF.md` records the latest verified state and remaining work.

## Release DoD (final)

1. Architecture docs committed and consistent with the code.
2. Real data pipeline verified (live records labeled `provenance: live`).
3. Analytical engine produces explainable scenarios from traceable inputs.
4. Web product functional (analytical + admin workflows).
5. Plans/pricing configurable via Super Admin.
6. Mobile source exists, shares the API contract, has build instructions.
7. Notification flow implemented; delivery verification reported honestly.
8. Auth/permissions/user-isolation tested.
9. Fresh-install verification documented.
10. Paid services are either absent or explicitly optional for the buyer.

## Anti-DoD (never acceptable)

- ✔ existed in docs but was never implemented — claims completion.
- ✔ replaced failing tests with weaker assertions to pass CI.
- ✔ committed live credentials or hardcoded secrets.
- ✔ declared a deployment/push successful without verifying it.
- ✔ presented demo data as real market data.