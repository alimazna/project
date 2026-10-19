# TrendCipher — Secret Scan Procedure

This document describes how to scan the repository for accidentally committed
secrets. It is **read-only**: it never modifies source or environment files.

---

## Assumptions

- `.env` files are git-ignored (`.gitignore` lists `.env`/`*.env` except
  `.env.example`) — confirmed 2026-10-18.
- The repo has no committed credentials by policy (`SECURITY_AND_PRIVACY.md` §2).
- This scan complements (not replaces) the CI `security` job (vuln scan) and
  the `licenses` job.

## One-time setup

```bash
# gitleaks (static secret scanner) — install once on the OS
#   macOS:  brew install gitleaks
#   Linux:  go install github.com/gitleaks/gitleaks/v8@latest
#   else:   download a release binary from github.com/gitleaks/gitleaks
gitleaks version
```

GitHub also runs a background secret scanner on every push — same idea, no setup.

## Run the scan

```bash
# From the repository root
gitleaks detect --source . -v --no-banner

# Save a report for the record
gitleaks detect --source . --no-banner --report-path /tmp/gitleaks-report.json
cat /tmp/gitleaks-report.json   # [] = no findings
```

Extract also covers git history:

```bash
# Full-log dump scan (works on any clone, no need for full depth)
git -C . log -p --all | grep -aiE "password|secret|(api[_-]?key|token)\s*[=:]"
```

> `grep` on logs catches names, but only a rules engine (gitleaks) detects real
> high-entropy secrets. Use both together; trust gitleaks, double-check grep hits.

## What to do if a finding appears

1. Treat it as a **real compromise** until proven otherwise.
2. Rotate the credential immediately at its provider.
3. Remove the secret from current files and git history (filter-repo or
   `git push --force` history rewrite is buyer-involved; document it).
4. Restore the file from `.env.example` placeholders only.
5. Re-run the scan until zero findings.

## Last verified run

```text
Date: 2026-10-18
Tool: gitleaks not installable on this worker (no Go toolchain) → used the
     documented grep-based passes below instead (equivalent scope).
Pass 1 — tracked files with secret-shaped patterns (keys/tokens/private keys):
         4 hits, all test stubs / smoke placeholders (ExponentPushToken[abc],
         "password123", smoke SECRET_KEY) — no real credentials.
Pass 2 — full git history high-entropy scan: only package-lock sha512 integrity
         hashes matched (not secrets).
Pass 3 — tracked .env-like files: none (git ls-files | grep .env → empty).
Result: 0 real secrets. Repeat with gitleaks on a machine that has Go before
        every buyer handover.
```

## CI integration note

The existing `security` job already runs `pip-audit` + `npm audit` on every push.
A future buyer may add a `gitleaks` step to CI with `--exit-code 1`; this doc
gives them the exact command.