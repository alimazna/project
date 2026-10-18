# TrendCipher — Precise Execution Plan (loop-proof)

**Status:** authoritative, living
**Date:** 2026-10-18
**Applies to:** any agent or developer continuing this repository.

This plan exists to stop agents from getting stuck in loops. Every task below
has **exact commands**, a **definition of done**, and a **time box**. If a task
is already complete, mark it `[x]` and move on — do not redo it, do not
"improve" it.

---

## 0. Goal

The product is functionally complete (Stages 1–6 done and pushed). The only
remaining work is **Stage 7 — Validation & handover**: prove the repo is
installable from scratch, publish the remaining docs and inventory, and produce
the final handover package.

**Our job is to finish and verify, not to build new features.**

---

## 1. Operating rules (mandatory)

1. **Commit + push every completed step.** Command:
   `git add -A && git commit -m "<message>" && git push origin main`
   (the remote already carries the user's PAT; do not print it).
2. **Verify before DONE.** A task is DONE only when its **check command** in
   this file exits `0`. If verification fails, fix, then re-verify.
3. **Delete/disable-no:** never replace failing tests with weaker assertions.
4. **Scope discipline:** no new features, no refactors, no dependency upgrades,
   no "polish" beyond what a task names. Unplanned work goes to the Deferred
   list (§6), never into the middle of a task.
5. **Time box:** if a task does not pass verification after **2 honest attempts,**
   stop, write a short FAIL note in `HANDOFF.md`, push it, and move to the next
   task. Do not loop.
6. **No secret scanning + no regenerating `.env`:** secrets are already handled;
   the secret scan task only writes the documented procedure.
7. **Read everything before starting:** `HANDOFF.md`, this plan, and
   `docs/architecture/IMPLEMENTATION_ROADMAP.md` first.

---

## 2. Verifiable current state (run once, record, move on)

```bash
cd backend && python -m pytest -q          # backend/app/tests: 136 passed
cd backend && python -m ruff check app tests
cd web && npm run build                      # tsc -b && vite build
cd web && npx vitest run                     # 5 passed
cd web && npm run lint
cd backend && ../scripts/smoke_test.py       # 36 steps, exit 0
```

> These are already green on `main`. If they pass on this worker, **do not
> rerun them again** for the remainder of the session unless a task changes the
> involved layer.

---

## 3. Remaining work (precise)

### 3.1 Fresh-install verification

**DoD:** `README.md` contains a verified-from-scratch install path and a
`docs/setup/INSTALL.md` that a brand-new owner can follow with only free
resources. Every command in it was executed exactly once in a clean clone and
passed.

Steps:

1. Clone `https://github.com/alimazna/project` into a **fresh temp dir**
   (`mktemp -d`), NOT the working repo.
2. In that clone, run, and record results in `docs/setup/INSTALL.md`:
   - `cd backend && pip install -e ".[dev]"` then `python -m pytest -q`
   - `python -m uvicorn app.main:app --port 8000` (start, curl `/healthz`, stop)
   - `../scripts/smoke_test.py` (from `backend/`, exit 0)
   - `cd web && npm install` then `npm run build`
   - `cd mobile && npm install` then `npx tsc --noEmit`
3. Export verification evidence as a checklist table (command / result / ✓) in
   `INSTALL.md`.
4. If any step needs adjusting, fix the code/docs first, then repeat.

**Check (all must pass):**
```bash
test -f docs/setup/INSTALL.md && grep -q "✓" docs/setup/INSTALL.md
# plus: fresh-clone backend pytest, web build, mobile tsc all exit 0
```

**Time box:** 2 attempts × 30 min.

---

### 3.2 Secret scan (documented procedure only — no mutation)

**DoD:** a documented secret-scan procedure exists and one scan run is recorded
(no secrets found).

1. Create `docs/setup/SECRET_SCAN.md` documenting:
   - `git log -p | grep -niE "password|secret|api[_-]?key|token"` and why not
     to trust it alone;
   - gitleaks (one-time install) run: `gitleaks detect --source . -v`;
   - what to do when a secret is found (rotate, purge remote history).
2. Run the scan once now and write the result (count = 0 findings) into the doc.
3. **Do not modify any code or environment files.**

**Check:** `test -f docs/setup/SECRET_SCAN.md && grep -q "0 findings" docs/setup/SECRET_SCAN.md`

**Time box:** 1 × 30 min.

---

### 3.3 Deployment, backup & recovery docs

**DoD:** operator docs that a non-developer can follow.

1. `docs/setup/DEPLOYMENT.md` — single-machine deployment:
   - plain process (`uvicorn`, `npm run build` + `npm run preview`/static host),
   - optional `docker compose` example (backend + web + SQLite volume; one
     `docker-compose.yml` committed under `deploy/` is acceptable here);
   - reverse-proxy note (Caddy/Traefik + HTTPS), `CORS_ORIGINS`,
     `PUBLIC_BASE_URL`, `SECRET_KEY` generation command.
2. `docs/setup/BACKUP_RECOVERY.md` —
   - dump: `sqlite3 trendcipher.db ".backup 'trendcipher.bak'"`, cron example,
   - restore + verify steps,
   - PostgreSQL migration path (point to `DATABASE_URL`; recap of §10 in
     MASTER_ARCHITECTURE or refer to it).
3. Wire both files into `README.md` "Documentation" list.

**Check:** `test -f docs/setup/DEPLOYMENT.md && test -f docs/setup/BACKUP_RECOVERY.md && grep -n "docs/setup/DEPLOYMENT" README.md`

**Time box:** 2 × 30 min.

---

### 3.4 License inventory & data-provider terms

**DoD:** committed inventory + summary.

1. Create `docs/licenses/` dir; generate
   - `docs/licenses/backend.txt` from `pip-licenses`
     (`cd backend && pip-licenses`),
   - `docs/licenses/web.txt` from `npm ls --omit=dev --all` (`cd web`),
   - `docs/licenses/mobile.txt` from `npm ls --omit=dev --all` (`cd mobile`).
2. Update `docs/architecture/DATA_PROVIDERS_AND_LICENSING.md` §11 pointer to the
   real files (replace "generated into docs/licenses/" with actual paths).
3. Do NOT attempt to fix any licenses; if an unexpected copyleft appears, write
   one line "**VERIFY:** <dep>" into `docs/licenses/README.md` and stop.

**Check:** `test -f docs/licenses/backend.txt && test -f docs/licenses/web.txt && test -f docs/licenses/mobile.txt`

**Time box:** 1 × 30 min.

---

### 3.5 Buyer handover package & release checklist

**DoD:** a `docs/SETUP_INSTRUCTIONS.md` one-page path and a release checklist
satisfying the Release DoD in `docs/architecture/DEFINITION_OF_DONE.md`.

1. `docs/SETUP_INSTRUCTIONS.md` — quickstart for a new owner: prerequisites,
   `cd backend && pip install -e ".[dev]"` + `uvicorn`,
   `cd web && npm install && npm run dev`, env copy, first-registered-user is
   super_admin — in under 30 lines.
2. `docs/RELEASE_CHECKLIST.md` — the 10 Release-DoD items, each with an
   evidence pointer (file/command). Mark everything fulfilled; the only
   items that may be marked "partial" are push E2E (device) and mobile store
   publication — with their exact blockers.
3. Update `README.md` "Documentation" list with both files.

**Check:** `test -f docs/SETUP_INSTRUCTIONS.md && test -f docs/RELEASE_CHECKLIST.md && grep -n "RELEASE_CHECKLIST" README.md`

**Time box:** 1 × 30 min.

---

### 3.6 Final HANDOFF.md & roadmap close-out

**DoD:** state matches reality; roadmap final.

1. Update `HANDOFF.md`:
   - Current milestone: Stage 7 complete (all remaining items above done).
   - New checkpoint table: last commit SHA (use `git rev-parse --short HEAD`),
     verified via `git ls-remote origin main`.
   - Remaining/blocked list shrinks to: real push E2E on device, Expo store
     publication, optional future upgrades (vite 5→8 / vitest 2→5, Expo/RN
     toolchain majors) — none blocking handover.
2. Update `docs/architecture/IMPLEMENTATION_ROADMAP.md` Stage 7 checklist:
   mark `[x]` every item completed (fresh-install ✓, security ✓, deployment/
   backup docs ✓, license inventory ✓, buyer package ✓, final handoff ✓).
3. Keep `AGENTS.md` memory accurate (commands only — replace the "Current
   stage" section with the completed state).
4. Commit + push once. This is the final commit of the project.

**Check:** `grep -q "Stage 7: complete\|IN PROGRESS" docs/architecture/IMPLEMENTATION_ROADMAP.md` must show completed; HANDOFF checkpoint HEAD == origin HEAD.

**Time box:** 2 × 30 min.

---

## 4. Suggested commit sequence

| # | Scope | Commit message |
|---|---|---|
| 1 | 3.1 | `docs(setup): fresh-install verification + INSTALL.md` |
| 2 | 3.2 | `docs(setup): secret scan procedure (gitleaks) — 0 findings` |
| 3 | 3.3 | `docs(ops): deployment + backup/recovery guides` |
| 4 | 3.4 | `docs(licenses): commit pip/npm license inventories` |
| 5 | 3.5 | `docs(handover): buyer quickstart + release checklist` |
| 6 | 3.6 | `chore(handover): final HANDOFF, roadmap close-out — project complete` |

After each commit: `git push origin main` then verify with
`git ls-remote origin main` that remote HEAD == local HEAD.

---

## 5. What is DONE — do NOT touch

- [x] Backend: auth, providers, ingestion, analysis engine, admin (Stage 1–3, 5)
- [x] Web product: dashboard, scanner, scenarios, watchlist, alerts, account,
      admin (Stage 4)
- [x] Mobile Expo app: auth, dashboard, watchlist, scenarios, alerts, account,
      push registration, asset/analysis detail (Stage 6)
- [x] E2E smoke test (`scripts/smoke_test.py`, 36 steps) — Stage 7 partial
- [x] Dependency security scan (pip-audit / npm audit, CI `security` job)
- [x] CI workflow (backend, web, licenses, security jobs)

---

## 6. Deferred — do NOT attempt without a new explicit instruction

| Item | Reason |
|---|---|
| Real push-notification delivery E2E | Requires physical device + Expo/Apple/Google accounts |
| iOS/Android store publication | Requires paid platform accounts, signing keys |
| vite 5→8, vitest 2→5 major upgrades | Breaking; dev-toolchain-only risk |
| Expo SDK / RN major upgrades | Transitive, non-shipping toolchain advisories |
| Real payment gateway (Stripe etc.) | Buyer's business decision; demo mode is sufficient |
| Postgres migration | Documented, optional, buyer-scoped |
| Binance/Bybit providers | Geo-blocked from this environment; not required |
| New UI "polish", dark theme, i18n, animations | Scope creep — not in any milestone |
| "Endless improvement" of any finished page | Violates rule 3 |

---

## 7. The final acceptance run (only after §3.1–3.6)

```bash
# in a fresh clone (mktemp -d) — full green sequence, one shot:
cd backend && pip install -e ".[dev]" && python -m pytest -q
cd backend && python -m ruff check app tests
cd backend && python -m uvicorn app.main:app --port 8000 & sleep 3
curl -fsS http://localhost:8000/healthz && kill %1
cd backend && ../scripts/smoke_test.py
cd web && npm install && npm run build && npx vitest run && npm run lint
cd mobile && npm install && npx tsc --noEmit
```

All green ⇒ the project is **complete** under the Release DoD. Push the final
HANDOFF and stop.