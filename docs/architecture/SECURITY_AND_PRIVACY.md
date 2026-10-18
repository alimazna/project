# TrendCipher — Security and Privacy

**Status:** Baseline
**Date:** 2026-10-17

---

## 1. Threat Model (summary)

| Threat | Mitigation |
|---|---|
| Credential theft / secret leak | Secrets only in env vars; never in git; no privileged keys in client bundles |
| Unauthorized access to other users' data | Backend-scoped queries by user id; RBAC enforcement server-side |
| Brute-force login | Argon2id hashing + rate limiting on auth endpoints |
| Session hijacking | Short-lived signed access tokens + revocable refresh tokens |
| Admin privilege escalation | Role checks on every admin endpoint; audit trail |
| Injection (SQL/NoSQL/keys) | Parameterized SQL via SQLAlchemy; input validation via Pydantic |
| Supply chain | Dependency pinning; CI license + vulnerability scan |
| Data interception | HTTPS everywhere in production; secure cookie flags |
| Log leakage | Structured logging that redacts secrets, emails, tokens |

---

## 2. Secrets and Configuration

- `.env` is never committed. `.env.example` ships with placeholder values only.
- Secret manager pattern: at runtime, all secrets come from environment
  variables. A future buyer may substitute a real secret manager; the config
  loader (`backend/app/core/config.py`) supports it.
- The development `.env.example` includes:
  - `SECRET_KEY` placeholder
  - `DATABASE_URL`
  - `JWT_TTL`, `REFRESH_TTL`
  - Optional provider credentials: `OKX_API_KEY` (unused w/ public data),
    `EXPO_ACCESS_TOKEN` (optional push)
  - `PUBLIC_BASE_URL`

## 3. Authentication

- **Hashing:** Argon2id (argon2-cffi). Passwords never stored in plain text or
  reversible form.
- **Tokens:** access JWT (signed, short TTL) + opaque refresh token stored in DB
  (revocable, rotates on use).
- **Login rate limiting:** exponential backoff per account/IP via in-process
  limiter (DB-backed for correctness).
- **Registration:** `user` role by default. First-run bootstrap creates
  `super_admin` from a documented CLI/env flow (no universal default
  credentials).

## 4. Authorization (RBAC)

| Role | Allowed |
|---|---|
| `user` | Own watchlists/alerts/profile/data |
| `admin` | Read users, health, diagnostics; scoped user management |
| `super_admin` | Everything incl. plans, settings, audit, deletion workflows |

Every admin endpoint calls `require_role(...)` middleware. Frontend buttons are
never the authorization boundary.

## 5. User Isolation

- All user-owned record queries include `WHERE user_id = current_user.id`.
- API responses never leak other users' IDs, emails, or hashes.
- Integration tests assert user A cannot read user B data.

## 6. Input Validation

- Pydantic schemas validate shapes, ranges, types on every endpoint.
- HTML escapes applied where user content is rendered (React default escaping).
- Sizes/limits enforced (e.g., watchlist item counts, alert payloads).

## 7. Administrative Actions

- Every admin mutation writes an `audit_events` row:
  `admin_id, action, target_type, target_id, before, after, created_at`.
- Audit events are append-only and viewable by `super_admin`.

## 8. Data Privacy

- We store only what the app needs: account identifiers, hashed credentials,
  watchlists, alerts, usage. No financial card data (payments are out-of-scope or
  handled by the buyer's provider).
- User deletion flow: purge personal data or anonymize per plan; documented.
- Logs do not contain emails, tokens, or news payloads by default (only IDs).

## 9. CORS, Headers, and TLS

- CORS origins configurable via env (`CORS_ORIGINS`), default `*` only in dev.
- Production: strict allowlist, HSTS, no mixed content; HTTPS terminated at the
  buyer's reverse proxy.

## 10. Dependency Security

- CI runs `pip-audit` (installed backend, incl. dev deps) and `npm audit
  --omit=dev` (web production deps) in the `security` job, plus a per-run
  license inventory in the `licenses` job.
- Verified 2026-10-18:
  - Backend `pip-audit`: **no known vulnerabilities** (the editable
    `trendcipher-backend` package is skipped as it is not on PyPI).
  - Web production (`npm audit --omit=dev`): **0 vulnerabilities** after
    upgrading `react-router-dom` 6.26.0 → 7.18.4 (fixes GHSA-wrjc-x8rr-h8h6 /
    GHSA-337j-9hxr-rhxg). Build/lint/tests stay green on v7.
  - Web dev-tooling (`vitest`, `vite`, `esbuild`, `tinypool`): moderate–critical
    advisories exist but are **dev-server/test-runner only** (not shipped);
    remediation requires a breaking major bump (vite 5→8, vitest 2→5) tracked as
    a buyer/next-milestone item.
  - Mobile (`expo`/`react-native` 58): 25 transitive advisories in the **Expo/RN
    build toolchain** (`@expo/cli`, `metro`, `node-forge`, `braces`,
    `micromatch`); none ship in the app bundle. `npm audit fix` auto-patched the
    patched transitive packages; the remainder require Expo/RN major upgrades
    and are tracked as a buyer item.

## 11. Known Unfinished Security Checks (tracked)

| Check | Status |
|---|---|
| Dependency vulnerability scan | DONE — CI `security` job + manual run 2026-10-18; remaining items are dev-toolchain-only or require breaking major bumps |
| Web dev tooling (vite/vitest) major upgrade | Tracked — breaking bump (vite 5→8, vitest 2→5); dev-server-only risk |
| Mobile Expo/RN toolchain major upgrade | Tracked — transitive, non-shipping; requires Expo/RN major bump |
| Real-device push token security | Blocked on physical device; code review done |
| Production TLS config | Docs provided; not exercised over public internet here |
| Full third-party data-redistribution legal review | Requires legal counsel; documented as buyer item |

## 12. Default Credentials Policy

- There are **no** universal default credentials.
- `scripts/bootstrap_admin.py` creates the first `super_admin` using a password
  supplied via env/interactive prompt, never a hard-coded value.