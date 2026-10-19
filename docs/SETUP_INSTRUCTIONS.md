# TrendCipher — Setup Instructions (from scratch)

Step-by-step for a new owner: **bare OS → app running with the first admin user**.

---

## 0. Requirements

| Requirement | Version | Notes |
|---|---|---|
| OS | Linux/macOS | Windows via WSL2 recommended |
| Docker | ≥ 24 | includes Compose v2 |
| Git | ≥ 2.30 | – |
| Node (optional, dev) | ≥ 20 | web dev; not needed for Compose run |
| Python (optional, dev) | 3.13 | backend dev; not needed for Compose run |

## 1. Get the code

```bash
git clone <your-repo-url> project && cd project
```

## 2. Configure secrets

```bash
cp deploy/.env.example .env
openssl rand -hex 32      # generate SECRET_KEY
# edit .env → SECRET_KEY=<output>, CORS_ORIGINS=http://localhost, PUBLIC_BASE_URL=http://localhost
```

## 3. Launch

```bash
docker compose -f deploy/docker-compose.yml up -d --build
docker compose -f deploy/docker-compose.yml ps        # backend (healthy), web, worker
```

Wait for `backend` to become `(healthy)` — the web waits on it.

## 4. Verify

```bash
curl -fsS http://localhost/healthz        # {"status":"ok",...}
curl -fsS http://localhost/api/v1/plans   # JSON list of plans
curl -fsS -o /dev/null -w "%{http_code}\n" http://localhost/login   # 200 SPA
```

## 5. First admin user

1. Open `http://localhost/register`.
2. Create an account. The **first user** becomes `super_admin` automatically.
3. Sign in and open **Admin** (top nav) → users/plans/ingestion/system.

## 6. Wire a domain + HTTPS (do before real users)

See `docs/setup/DEPLOYMENT.md` → “Reverse proxy / HTTPS”. Minimum:

- TLS terminator (Caddy snippet provided there) in front of port 80.
- `.env`: `PUBLIC_BASE_URL=https://yourdomain.com`, `CORS_ORIGINS=https://yourdomain.com`.
- Restart: `docker compose -f deploy/docker-compose.yml up -d`.

## 7. Rebrand (optional early or late)

`docs/REBRAND.md` — a single `VITE_APP_NAME` in `web/.env` then rebuild:
`cd web && VITE_APP_NAME=YourName npm run build` (or set the env in CI).

## 8. Talk to the market (fees / limits sanity check)

- Plans are seeded (free, growth, pro) in `backend/app` — edit pricing in the
  admin UI or directly in the seed file, then rebuild the image.
- News feeds default to CoinTelegraph + CoinDesk RSS.
- Market data: Kraken primary (free public endpoints used) — see
  `docs/architecture/DATA_PROVIDERS_AND_LICENSING.md` for limits and the
  exact endpooint coverage.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `backend` restarting | wrong `SECRET_KEY` type? | ensure it’s ≥32 chars |
| `Cannot connect to Docker daemon` | daemon not running | `sudo systemctl start docker` |
| Port 80 busy | another server | change web ports in compose |
| CORS/API errors in browser | `CORS_ORIGINS` missing the site origin | add it and `up -d` |
| `Database is locked` | two processes writing | SQLite single-instance: keep ONE backend+worker pair per volume |
| See API in backend logs ok but web 502 | proxy target `backend:8000` unavailable | `docker compose logs backend`; check health |

## Done → next

The full operational picture is in `docs/setup/` and the owner walk-through in
`docs/BUYER_PACKAGE.md`. For a launch checklist see `docs/RELEASE_CHECKLIST.md`.