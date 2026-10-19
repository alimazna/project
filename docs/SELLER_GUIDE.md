# TrendCipher — Seller Guide

How to position, package, and sell this product — written for the current owner.

---

## 1. What you’re really selling

**A complete, runnable product, not a code dump.** Your differentiators:

1. **Explainable analysis** — every scenario ships with *why*: a list of rule
   drivers with rationale, alignment scores, entry/stop/targets, and rule-versioning.
   Nothing else in the crypto-news niche does deterministic, auditable output.
2. **Closed-source-ready but permissively licensed deps** — Apache-2.0/MIT only;
   no copyleft exposure for the buyer.
3. **Three surfaces from one codebase** — API, web SPA, and Expo mobile app
   (auth, watchlist, alerts with in-app push). A small team can white-label it.
4. **One-command deployment** — a non-engineer can run the whole stack with
   `docker compose up` and a `.env`.
5. **Tested on the way out** — 136 backend tests + 36-step E2E smoke + 11 web
   tests; CI keeps it green.

## 2. Positioning options (pick per buyer)

| Buyer profile | Angle |
|---|---|
| Full‑stack agencies / dev shops | White-label SAS starter: rebrand → deploy → resell to clients; they own margin via hosting |
| Crypto newsletters / signal sellers | Replace their manual Telegram channel with a branded web+app product that *explains* signals |
| Influencers monetizing trading | Their audience wants tools, not Discord chaos; this is the app behind the brand |
| Startups pivoting into fintech | Fastest compliant MVP — real auth, billing plans, admin, push, charts |

## 3. The 10-minute demo script

```text
1. Open the deployed web app → landing page (value prop visible in 2s).
2. Register → first user = super_admin (shows ownership model).
3. Dashboard: ticker strip → scenario card has Entry/Stop/Targets + “Why?” drivers.
4. Open an asset detail → chart with overlaid Entry/Stop/TP levels.
5. Show mobile (Expo Go or built app): same data, push-ready account screen.
6. Close with API explorer: /docs (FastAPI) — buyers love a real API.
```

## 4. Pricing the sale (heuristic)

- Value = the hours you saved × their hourly rate + the unfair advantage
  (a working 3-surface product with tests and deployment).
- Common anchors: **starter/hobby $300–900**, **white-label with source
  $1,500–5,000**, **done-for-you deployment + support $800+/mo**.
- Never underprice the mobile app — the physical-device push path is the costliest
  to replicate.

## 5. Sale-enablement checklist (each = a real file)

- [x] `docs/BUYER_PACKAGE.md` — the “start here” map.
- [x] `docs/SETUP_INSTRUCTIONS.md` — from-scratch runbook.
- [x] `docs/RELEASE_CHECKLIST.md` — professional, launchable signals.
- [x] `docs/REBRAND.md` — “we can white-label it for you” proof.
- [x] `docs/setup/DEPLOYMENT.md`, `BACKUP_RECOVERY.md`, `SECRET_SCAN.md` — ops maturity.
- [x] `docs/licenses/LICENSE_SUMMARY.md` — legal diligence done.
- [ ] **Pre-sale punch list** (run before handing keys):
      - [ ] Rebranded demo instance on your own domain.
      - [ ] `.env` in the demo has a **fresh** SECRET_KEY.
      - [ ] Expo Go / side-loaded APK path documented for the buyer
            (`docs/setup/EXPO_GO_HOWTO.md`) — store publishing is intentionally out of scope.
      - [ ] Terms/privacy placeholder pages filled if the buyer is launching publicly.

## 6. Handling the “is it real?” question

> “It was built as a production-oriented product, not a tutorial. Proof:
> 136 tests in the backend, a 36-step end-to-end API journey, a live Docker
> stack with healthchecks, license and secret audits, and CI. You can run it
> in 10 minutes and I’ll include onboarding.”

## 7. After-sale

- Hand over the `docs/` tree as the operating manual (it is the manual).
- Offer a 30-day support window at a fixed fee (or up-front retainer).
- Transfer the GitHub repo under their organization, or archive on your side and
  hand a tarball — clarify before closing so nothing is lost in expectations.