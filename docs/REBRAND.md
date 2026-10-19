# TrendCipher — Rebranding Guide (5-minute path)

The product name, short tagline, and tone are **config- and theme-driven**. A
buyer can replace the visible brand without touching a single component.

---

## 1. Change the product name (web)

**One value** drives the header logo, the landing-page sentence, and the
browser tab title:

```bash
# in web/.env (or build environment):
VITE_APP_NAME=YourName
```

- The header logo splits the name on camelCase: `YourName` renders as
  `Your<span>Name</span>`; `TrendCipher` renders as `Trend<span>Cipher</span>`.
  Use camelCase to mark a highlighted tail, e.g. `AcmeCoin`, `PulseSight`.
- Then rebuild: `cd web && npm run build`.

Verified 2026-10-18: `VITE_APP_NAME=PulseSight` produces a bundle containing
`PulseSight` and the build passes.

## 2. Change the mobile name (Expo)

Edit `mobile/app.json`:

```jsonc
{
  "expo": {
    "name": "YourName",
    "slug": "yourname"
  }
}
```

Then `npx expo prebuild` (or `npx expo run:android` / `run:ios`) regenerates the
native projects with the new display name. This is a one-line change per build;
no code edits needed.

## 3. Colors and fonts (web)

All design tokens live in `web/src/styles/global.css` as CSS variables
(worked example below). Change just these to restyle the app:

```css
:root {
  --c-primary: #4f8cff;      /* primary brand color */
  --c-bg: #0b0e14;           /* background */
  --c-text: #e6ebf5;         /* foreground */
  --c-accent: #22c55e;       /* highlights, badges (bull) */
}
```

Typefaces and spacing are also centralized at the top of the same file.

## 4. Favicon / logo slots

- `web/public/favicon.svg` — browser tab icon (create one and drop it in).
- `mobile/assets/icon.png`, `mobile/assets/splash-icon.png`, and
  `mobile/assets/adaptive-icon.png` — native icons (replace files, same names).
- `docs/BUYER_PACKAGE.md` — if you produce a logo pack, note it there.

## 5. Anything still showing the old name?

```bash
grep -rn "TrendCipher" --include="*.tsx" --include="*.ts" --include="*.html" --include="*.md" web/src web/index.html | grep -v node_modules
```

Remaining hits are intentional (comment banners in `global.css`/`api.ts`, the
default in `src/lib/config.ts`, and package metadata) — or the fallback default
when `VITE_APP_NAME` is unset. Nothing user-facing is hardcoded.

## 6. Legal/product name

- The repository name (`TrendCipher`) and domain are **not changed by env**.
- For a real launch, buy a domain and rename the repo — the codebase is
  otherwise brand-agnostic (checked 2026-10-18).