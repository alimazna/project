# TrendCipher — UI Design Skill Setup

## Installed skill

- **Name:** `frontend-design`
- **Location:** `.agents/skills/frontend-design/` (project-local, in this repository)
- **Files preserved:**
  - `SKILL.md` — skill instructions (4443 bytes, byte-for-byte identical to upstream)
  - `README.md` — skill README
  - `LICENSE.txt` — MIT license (copyright OpenHands, contact@all-hands.dev)
  - `.plugin/plugin.json` — plugin manifest metadata

## Source revision

- **Upstream repo:** https://github.com/OpenHands/extensions
- **Skill path:** `skills/frontend-design/`
- **Resolved commit SHA:** `22211a04023f0b9c90b56c294c8527ccea5fcf61`
  (verified via GitHub API: commits for path `skills/frontend-design`, head commit
  dated 2026-04-23, message "fix: add plugin manifest to iterate skill for codex compatibility (#202)")
- **Verification:** the cached copy in
  `/home/openhands/.openhands/cache/skills/public-skills/skills/frontend-design/SKILL.md`
  was diffed against the raw upstream file at that exact SHA and is **identical**
  (`diff -q` → no differences).

## License

MIT — the skill source is licensed under the MIT License. Full license text is
preserved in `.agents/skills/frontend-design/LICENSE.txt`.

## How the skill is discovered / invoked

This OpenHands session auto-discovers skills under `.agents/skills/` in the
repository root. For future UI/UX work, the agent should invoke it with the
skill loader, e.g. `invoke_skill(name="frontend-design")`, or it is triggered
automatically when the request involves building or styling web UI.

## When to use this skill (future UI/UX tasks)

Use it whenever the request involves:

- Web interfaces and application screens.
- Dashboards and administrative panels.
- UI visual refinement and redesign.
- Typography, spacing, color systems, and layout hierarchy.
- Responsive layouts for mobile, tablet, and desktop.
- Reusable frontend components and design systems.
- Forms, navigation, dialogs, notifications, and interaction states.
- Accessibility and keyboard navigation.
- Loading, empty, error, success, and disabled states.
- Visual consistency across multiple screens.

TrendCipher-specific design constraints that override the generic skill where
they conflict (from the founder's approved direction):

- Brand identity: `#0B0F17` background / `#FF2A55` electric red / `#2563EB`
  electric blue, glassmorphism + glow, slogan "Unlock Predictive Insight".
- A "human touch" layer is required: Caveat font for handwritten-style notes,
  margin notes, tilt buttons, live status line.
- Two products share this skill's output: the web app (`web/`, React + TS +
  Vite) and the mobile app (`mobile/`, Expo/React Native). Keep both visually
  consistent with the established identity.