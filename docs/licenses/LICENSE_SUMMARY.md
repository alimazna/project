# TrendCipher — Third-Party License Summary

Verification run: **2026-10-18**. All production dependencies use permissive
licenses. A full re-run command is included below so a buyer can refresh the
list at any time.

## Backend (Python) — `docs/licenses/backend.txt`

Verified with `pip-licenses` against the installed backend environment.
Dominant licenses: **MIT**, **Apache-2.0**, **BSD-2/3-Clause**, **PSF**.
Notable direct deps: FastAPI (MIT), SQLAlchemy (MIT), Pydantic (MIT),
Starlette (BSD-3-Clause), `argon2-cffi` (MIT), PyJWT (MIT).
⚠️ `pip-licenses` revealed transitive tooling (pip, setuptools, wheel…) because
the inventory was captured in the worker environment; production installs pull
only the app deps from `backend/pyproject.toml`.

## Web (Node) — `docs/licenses/web.txt`

Verified with `license-checker` (full tree, dev included). License distribution:

| License | Packages |
|---|---|
| MIT | 265 |
| ISC | 32 |
| Apache-2.0 | 21 |
| BSD-2-Clause | 9 |
| BSD-3-Clause | 4 |
| MIT-0 / BlueOak / CC0 / CC-BY / Python-2.0 | 7 |
| UNLICENSED | 1 (the project itself, `trendcipher-web`) |

`--failOn 'GPL;AGPL;LGPL;MPL;EPL'` returned **no copyleft hits**.

## Compliance notes

- **lightweight-charts** (Apache-2.0) — used in the web app; Apache-2.0 allows
  redistribution with license notice. The library LICENSE is preserved in
  `node_modules`; deployment keeps it in the bundle metadata. A NOTICE file is
  not required for Apache-2.0 ASF-licensed code when unchanged, but if the buyer
  redistributes the web app standalone, keep a copy of the license alongside.
- **expo ecosystem** — mobile deps are MIT/Apache-2.0 (Expo SDK). See
  `mobile/package-lock.json` for the full tree.
- **Fonts**: `Inter` is used via system fallback (no file redistribution);
  `SF Mono`/`Roboto Mono` are system fallbacks — no font files ship.
- **RSS/news**: content is fetched and *quoted/linked only* (CoinTelegraph,
  CoinDesk). Embedded full-text scraping would need their content policies.
- Icons: **Feather** (MIT) via `feather-icons` in web; `@expo/vector-icons`
  carries only ITS own license — no GPL icon fonts are bundled.

## Regenerate

```bash
# backend
cd backend && pip install pip-licenses && pip-licenses > ../docs/licenses/backend.txt

# web (temporary tool)
cd web && npm install --no-save license-checker
./node_modules/.bin/license-checker --production=false > ../docs/licenses/web.txt
./node_modules/.bin/license-checker --failOn 'GPL;AGPL;LGPL;MPL;EPL' --summary
#   (expect: no fatal output = copyleft-free; then `npm prune` to drop the tool)
```