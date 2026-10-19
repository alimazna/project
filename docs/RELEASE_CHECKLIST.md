# TrendCipher — Release Checklist

Use this before every public launch or big push. Each item links to the
playbook that explains it.

## A. Code & process

- [ ] `git pull` — working tree = latest `main`.
- [ ] Backend tests green: `cd backend && python -m pytest -q`
- [ ] Backend lints: `cd backend && python -m ruff check app tests`
- [ ] Web tests green: `cd web && npx vitest run`
- [ ] Web typecheck + build: `cd web && npx tsc -b && npm run build`
- [ ] Mobile typecheck: `cd mobile && npx tsc --noEmit`
- [ ] E2E smoke 36 steps: `python scripts/smoke_test.py` (from repo root)
- [ ] CI on GitHub **for the exact commit you ship** (Actions: backend, web, security).

## B. Security

- [ ] `.env` `SECRET_KEY` = fresh 32+ random bytes (`openssl rand -hex 32`).
- [ ] Secret scan clean: `gitleaks detect --source . --no-banner` (0 findings;
      procedure `docs/setup/SECRET_SCAN.md`).
- [ ] No API keys/credentials in git history (`git ls-files | grep -i env` empty).
- [ ] HTTPS in front; `CORS_ORIGINS` contains only the real origins.
- [ ] Receipts: run `pip-audit` + `npm audit` via the CI security job and check
      the run log for 0 high/critical.

## C. Data & operations

- [ ] Fresh clone deploys: `docker compose -f deploy/docker-compose.yml up -d --build`
      from a **clean machine** (test in a fresh sandbox).
- [ ] Backup tested: `docs/setup/BACKUP_RECOVERY.md` — restore into an empty volume
      and confirm `/healthz` + a registered user logs in.
- [ ] `PUSH_PROVIDER` decision: `log` (stub) or `expo` (real push). If `expo`,
      device test on Android + iOS done.
- [ ] Worker health observed over ≥ 24h: `docker compose logs -f worker` no
      unhandled loop errors.
- [ ] SQLite volume backup scheduled (cron) and off-machine copy confirmed.

## D. Brand & UX

- [ ] Rebrand applied where intended (`docs/REBRAND.md`): web name, mobile
      `app.json`, favicons, domain, repo name.
- [ ] Value-proposition copy updated everywhere user-facing (landing, pricing,
      mobile onboarding).
- [ ] Legal: **terms / privacy policy** page present and pointed from footer —
      required before real users (misplaced: not in codebase yet — add links).

## E. Final

- [ ] `HANDOFF.md` updated to this release (commit hash, what changed, what’s next).
- [ ] All release docs committed and pushed.
- [ ] Tag the release: `git tag v1.0.0 && git push --tags`.
- [ ] Announce with the release summary (see `docs/SELLER_GUIDE.md` §sell-pitch).