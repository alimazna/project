# OpenHands Skills Guide — TrendCipher SaaS Project

This guide documents the OpenHands skills installed into the TrendCipher SaaS
project (`alimazna/project`) for use in future development sessions.

Installation location (project-local): `.agents/skills/<skill-name>/`

---

## Installed Skills

### 1. add-skill
- **Purpose:** Import additional skills from GitHub; retrieve skill files and supporting resources; verify imported skills contain required instructions.
- **Installed at:** `.agents/skills/add-skill/`
- **Official source:** https://github.com/OpenHands/extensions/tree/main/skills/add-skill
- **Upstream commit SHA:** `804c84b590d53a6d16991c68bbe10aa2c5222748` (head commit for the path at install time)
- **Intended use in TrendCipher:** installing any future skill on request, from official or user-specified repos.
- **Invocation:** `invoke_skill(name="add-skill")`, or run `python3 .agents/skills/add-skill/scripts/fetch_skill.py "<github-url>" /workspace/project/project`.
- **Limitations:** installs project-locally into `.agents/skills/`, never globally; warns (does not overwrite) on existing skill unless `--force` is passed.

### 2. frontend-design
- **Purpose:** Improve visual quality of the SaaS interface; create distinctive, professional UI designs; improve typography, spacing, layout, color systems, and visual hierarchy; design responsive interfaces; improve dashboards, forms, navigation, and reusable components; avoid generic AI aesthetics and inconsistent design.
- **Installed at:** `.agents/skills/frontend-design/`
- **Official source:** https://github.com/OpenHands/extensions/tree/main/skills/frontend-design
- **Upstream commit SHA:** `22211a04023f0b9c90b56c294c8527ccea5fcf61` (verified earlier for `frontend-design`; identical content verified against cache)
- **Intended use in TrendCipher:** all UI/UX work — web (`web/`, React+TS+Vite) and mobile (`mobile/`, Expo/RN). Must respect the founder's approved identity: `#0B0F17` background, electric red `#FF2A55`, electric blue `#2563EB`, glassmorphism + glow, slogan "Unlock Predictive Insight", and the "human touch" layer (Caveat font, margin notes, tilt buttons, live status line).
- **Invocation:** `invoke_skill(name="frontend-design")` (auto-triggered on UI design requests).
- **Limitations:** preserve established product identity and existing API/state contracts while restyling.

### 3. security
- **Purpose:** Apply secure development practices; review authentication and authorization; protect customer data and sensitive configuration; identify insecure API access and input-validation problems; reduce risks with sessions, credentials, permissions, and data exposure.
- **Installed at:** `.agents/skills/security/`
- **Official source:** https://github.com/OpenHands/extensions/tree/main/skills/security
- **Upstream commit SHA:** `22211a04023f0b9c90b56c294c8527ccea5fcf61`
- **Intended use in TrendCipher:** review/implement auth, roles (user/admin/super_admin), subscription/billing, watchlists/alerts (user data), API inputs, secrets handling, and JWT/refresh-token flows.
- **Invocation:** `invoke_skill(name="security")` (or follow its guidance inline when security-relevant work is requested).
- **Limitations:** guidance-only skill; does not ship automation scripts.

### 4. github
- **Purpose:** Follow GitHub-specific repository workflows; work with branches, issues, pull requests, and GitHub Actions when authorized; preserve existing repository history and avoid unsafe git operations; keep changes isolated and reviewable.
- **Installed at:** `.agents/skills/github/`
- **Official source:** https://github.com/OpenHands/extensions/tree/main/skills/github
- **Upstream commit SHA:** `642df1af9444afdc50024ab5eaaa36f5f93ffd09`
- **Intended use in TrendCipher:** authorized repo management — push checkpoint commits per the founder's convention, create/update PRs, manage issues, inspect CI runs. Uses `GITHUB_TOKEN`.
- **Invocation:** `invoke_skill(name="github")` (auto-triggered when using GitHub). Prefer `gh`/GitHub API over the browser; never push to `main` without explicit authorization.
- **Limitations:** requires explicit user authorization for pushes/PRs; do not modify git config.

### 5. technical-writing
- **Purpose:** Produce clear technical documentation; explain system architecture and module responsibilities; document APIs, dependencies, configuration, and setup procedures; keep developer documentation understandable and maintainable.
- **Installed at:** `.agents/skills/technical-writing/`
- **Official source:** https://github.com/OpenHands/extensions/tree/main/skills/technical-writing
- **Upstream commit SHA:** `fc09aeff8aa92c19741fcc17d3d497540c39f942`
- **Intended use in TrendCipher:** docs/architecture files, README/HANDOFF, API docs, deployment and runbook updates.
- **Invocation:** `invoke_skill(name="technical-writing")` when the request involves documentation.
- **Limitations:** guidance-only skill.

### 6. code-review
- **Purpose:** Review code changes for substantive correctness and security issues; identify regressions, compatibility risks, and maintainability problems; verify findings against actual source files; report evidence-based findings without manufacturing problems or modifying code during a review-only task.
- **Installed at:** `.agents/skills/code-review/`
- **Official source:** https://github.com/OpenHands/extensions/tree/main/skills/code-review
- **Upstream commit SHA:** `aafc665345fa13d5f37910d15654e1322d17b264`
- **Intended use in TrendCipher:** reviewing a defined set of changes (PRs, commits) before merge; grounded verification against the actual source, with evidence.
- **Invocation:** `invoke_skill(name="code-review")` when reviewing a defined change set. Includes `commands/codereview.md` and `commands/codereview-roasted.md` sub-commands.
- **Limitations:** review-only; does not modify code during review.

### 7. agent-memory
- **Purpose:** Maintain useful repository-specific knowledge; document project structure, conventions, setup instructions, and workflows; help future OpenHands sessions understand established constraints; preserve long-term knowledge via AGENTS.md.
- **Installed at:** `.agents/skills/agent-memory/`
- **Official source:** https://github.com/OpenHands/extensions/tree/main/skills/agent-memory
- **Upstream commit SHA:** `22211a04023f0b9c90b56c294c8527ccea5fcf61`
- **Intended use in TrendCipher:** keeping AGENTS.md (at repo root) accurate — build/run commands, project conventions, stack facts, checkpoint rule. Includes `commands/remember.md` sub-command.
- **Invocation:** `invoke_skill(name="agent-memory")` with **explicit user confirmation** before writing newly learned information to AGENTS.md (the skill requires listing the exact items to save and obtaining approval).
- **Limitations:** existing repository instructions are not modified without authorization; user approval is required before saving new info to AGENTS.md.

---

## Recommended Usage Rules

1. Use **`frontend-design`** whenever the user explicitly requests UI/UX design or interface improvements.
2. Use **`security`** when implementing or reviewing authentication, authorization, subscriptions, user data, or API access.
3. Use **`github`** for authorized repository-management tasks.
4. Use **`technical-writing`** when documenting project architecture, APIs, setup, or deployment.
5. Use **`code-review`** when reviewing a defined set of changes.
6. Use **`agent-memory`** according to its instructions, with user approval before adding newly learned information to AGENTS.md.
7. Use **`add-skill`** when the user explicitly requests additional skill installation.

---

## Installation Method & Verification

- **Mechanism:** the official `add-skill` fetch script (`git` sparse checkout, `SKILL.md` validation, no arbitrary remote script execution). `frontend-design` was installed earlier from the verified upstream cache; the other six were installed with the official `fetch_skill.py`.
- **Verification:** each installed `SKILL.md` was compared (`diff -q`) against the upstream-verified cached copy and was **identical** for all seven skills.
- **Licensing:** the `frontend-design` skill ships `LICENSE.txt` (MIT); the other skills declare MIT-style licensing via `.plugin/plugin.json` metadata (`license: MIT`). Full license text is preserved where shipped.
- **No changes to the SaaS application:** no source files, dependencies, schemas, migrations, configs, CI, or deployment files were modified. `git status` shows only untracked `.agents/` and the documentation files.
- **Related doc:** `UI_SKILL_SETUP.md` (created earlier) documents the `frontend-design` skill installation in detail.

## Making the Skills Available in Future Sessions

Skills under `.agents/skills/` in the repository root are auto-discovered by
OpenHands in each new session working on this workspace. No restart or extra
step is required; future sessions can invoke them with the skill loader
(`invoke_skill(name="...")`) or rely on automatic triggers. If a skill is not
auto-discovered, double-check that the working directory is the repo root and
`.agents/skills/<skill>/SKILL.md` exists.