#!/usr/bin/env python
"""TrendCipher API-driven end-to-end smoke test (Stage 7).

Runs the full product journey against an isolated temporary SQLite database
using FastAPI's TestClient (no external services, no live network):

  health -> plans -> register (first user = super_admin) -> login -> me
  -> symbols -> candles -> tickers -> news -> analysis run -> watchlists
  -> alerts -> notification preferences -> devices -> subscriptions -> admin.

Usage:
    cd backend && ../scripts/smoke_test.py

Exit code is non-zero if any step fails. Logs a per-step PASS/FAIL line.
"""

from __future__ import annotations

import os
import sys
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Allow running from either repo root or backend/.
_BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(_BACKEND))

# Isolated database must be configured before app modules are imported,
# because SessionLocal binds to the engine at import time.
_SMOKE_DIR = tempfile.mkdtemp(prefix="trendcipher-smoke-")
_DB_URL = f"sqlite:///{os.path.join(_SMOKE_DIR, 'smoke.db').replace(os.sep, '/')}"
os.environ["DATABASE_URL"] = _DB_URL
os.environ.setdefault("SECRET_KEY", "smoke-test-not-a-real-secret")
os.environ.setdefault("PUSH_PROVIDER", "log")

from fastapi.testclient import TestClient  # noqa: E402

from app.core.ratelimit import reset_rate_limits  # noqa: E402
from app.db.session import init_engine  # noqa: E402
from app.main import app  # noqa: E402
from app.providers.base import CandleData  # noqa: E402
from app.services.ingestion import ensure_symbols, ingest_news, upsert_candles  # noqa: E402
from app.services.seed import seed_plans  # noqa: E402

PASSED: list[str] = []
FAILED: list[str] = []
API = "/api/v1"


def check(name: str, cond: bool, detail: str = "") -> None:
    """Record a smoke-test assertion result."""
    if cond:
        PASSED.append(name)
        print(f"  PASS  {name}")
    else:
        FAILED.append(name)
        print(f"  FAIL  {name}  {detail}")


def main() -> int:
    # --- isolated database ----------------------------------------------
    from sqlalchemy.orm import Session

    from app.db.session import Base, SessionLocal, engine

    init_engine()
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        seed_plans(Session(bind=conn))

    reset_rate_limits()

    with TestClient(app) as c:
        # --- public endpoints -------------------------------------------
        print("\n[public]")
        r = c.get("/healthz")
        check("healthz", r.status_code == 200 and r.json().get("status") == "ok", r.text)

        r = c.get(API + "/plans")
        body = r.json()
        check(
            "plans list",
            r.status_code == 200 and body.get("total", 0) >= 1 and len(body["items"]) >= 1,
            r.text,
        )
        plan_code = body["items"][0]["code"]

        # --- register (first user becomes super_admin) ------------------
        print("\n[auth]")
        email = "smoke@example.com"
        pw = "SmokeTest#123"
        r = c.post(
            API + "/auth/register",
            json={"email": email, "password": pw, "display_name": "Smoke Tester"},
        )
        body = r.json()
        check("register", r.status_code == 201 and bool(body.get("access_token")), r.text)
        access = body["access_token"]
        refresh = body.get("refresh_token")
        headers = {"Authorization": f"Bearer {access}"}

        r = c.post(API + "/auth/login", json={"email": email, "password": pw})
        body = r.json()
        check("login", r.status_code == 200 and bool(body.get("access_token")), r.text)

        r = c.get(API + "/auth/me", headers=headers)
        check(
            "me (super_admin)",
            r.status_code == 200
            and r.json().get("email") == email
            and "super_admin" in r.json().get("roles", []),
            r.text,
        )

        if refresh:
            r = c.post(API + "/auth/refresh", json={"refresh_token": refresh})
            check(
                "refresh rotation",
                r.status_code == 200 and bool(r.json().get("access_token")),
                r.text,
            )

        # --- market (seed deterministic data) ---------------------------
        print("\n[market]")
        db = SessionLocal()
        try:
            ensure_symbols(
                db,
                [{"symbol": "BTC/USD", "base": "BTC", "quote": "USD", "display_name": "Bitcoin"}],
            )
            t0 = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
            upsert_candles(
                db,
                [
                    CandleData(
                        "BTC/USD",
                        "1h",
                        t0 + timedelta(hours=i),
                        open=95000 + i * 10,
                        high=95000 + i * 10 + 50,
                        low=95000 + i * 10 - 50,
                        close=95000 + i * 10 + 10,
                        volume=100.0 + i,
                    )
                    for i in range(60)
                ],
            )
            ingest_news(
                db,
                [
                    {
                        "source": "CoinTelegraph",
                        "url": "https://example.com/smoke",
                        "title": "Smoke test article about Bitcoin",
                        "published_at": t0,
                        "assets": ["BTC/USD"],
                    }
                ],
            )
            db.commit()
        finally:
            db.close()

        r = c.get(API + "/market/symbols")
        symbols = r.json()["symbols"]
        check(
            "symbols",
            r.status_code == 200 and any(s["symbol"] == "BTC/USD" for s in symbols),
            r.text,
        )

        r = c.get(API + "/market/candles/BTC/USD?interval=1h&limit=60")
        check(
            "candles",
            r.status_code == 200 and len(r.json()["candles"]) == 60,
            r.text,
        )

        r = c.get(API + "/market/tickers")
        check("tickers", r.status_code == 200 and isinstance(r.json().get("tickers"), list), r.text)

        r = c.get(API + "/market/news?limit=5")
        articles = r.json().get("articles", [])
        check("news", r.status_code == 200 and len(articles) >= 1, r.text)

        r = c.get(API + "/market/news?source=CoinTelegraph")
        check(
            "news source filter",
            r.status_code == 200
            and all(a["source"] == "CoinTelegraph" for a in r.json()["articles"]),
            r.text,
        )

        # --- analysis ----------------------------------------------------
        print("\n[analysis]")
        r = c.post(API + "/analysis/run?symbol=BTC/USD&interval=1h&limit=60&with_news=true")
        body = r.json()
        scenario = body.get("scenario", {})
        check(
            "analysis run",
            r.status_code == 200
            and "direction" in scenario
            and "rule_version" in scenario
            and "evidence" in scenario,
            r.text,
        )
        saved_id = body.get("saved_scenario_id")
        check("scenario persisted", saved_id is not None, r.text)

        r = c.get(API + "/analysis/scenarios?symbol=BTC/USD")
        check(
            "scenarios list",
            r.status_code == 200
            and any(s["id"] == saved_id for s in r.json()["scenarios"]),
            r.text,
        )

        if saved_id:
            r = c.get(API + f"/analysis/scenarios/{saved_id}")
            body = r.json()
            check(
                "scenario detail",
                r.status_code == 200 and body.get("scenario", {}).get("id") == saved_id,
                r.text,
            )

        r = c.get(API + "/analysis/backtest?symbol=BTC/USD&interval=1h&limit=60")
        body = r.json()
        check(
            "backtest",
            r.status_code == 200
            and isinstance(body.get("results"), list)
            and body.get("stats", {}).get("trades") >= 1,
            r.text,
        )

        # --- authenticated user features --------------------------------
        print("\n[watchlists]")
        r = c.post(API + "/watchlists", json={"name": "Smoke", "symbols": ["BTC/USD"]}, headers=headers)
        wl = r.json().get("watchlist", {})
        check("create watchlist", r.status_code == 201 and wl.get("name") == "Smoke", r.text)
        wl_id = wl.get("id")

        r = c.get(API + "/watchlists", headers=headers)
        check("list watchlists", r.status_code == 200 and len(r.json()["watchlists"]) >= 1, r.text)

        if wl_id:
            r = c.put(API + f"/watchlists/{wl_id}", json={"symbols": ["BTC/USD"]}, headers=headers)
            check("update watchlist", r.status_code == 200, r.text)

        print("\n[alerts]")
        r = c.post(
            API + "/alerts",
            json={"symbol": "BTC/USD", "kind": "price_above", "value": 200000, "cooldown_minutes": 60},
            headers=headers,
        )
        alert = r.json().get("alert", {})
        check("create alert", r.status_code == 201 and alert.get("kind") == "price_above", r.text)
        alert_id = alert.get("id")

        r = c.get(API + "/alerts", headers=headers)
        check("list alerts", r.status_code == 200 and len(r.json()["alerts"]) >= 1, r.text)

        if alert_id:
            r = c.post(API + f"/alerts/{alert_id}/evaluate", headers=headers)
            check("evaluate alert", r.status_code in (200, 201), r.text)
            r = c.delete(API + f"/alerts/{alert_id}", headers=headers)
            check("delete alert", r.status_code == 204, r.text)

        print("\n[notification prefs + devices]")
        r = c.put(
            API + "/notification-preferences",
            json=[
                {"category": "price_alerts", "channel": "push", "enabled": True},
                {"category": "news_alerts", "channel": "push", "enabled": True},
            ],
            headers=headers,
        )
        prefs = r.json().get("preferences", [])
        check("set prefs", r.status_code == 200 and len(prefs) >= 2, r.text)

        r = c.get(API + "/notification-preferences", headers=headers)
        check("get prefs", r.status_code == 200 and len(r.json().get("preferences", [])) == 4, r.text)

        r = c.post(
            API + "/devices",
            json={
                "platform": "android",
                "push_token": "ExponentPushToken[smoke-test-1234]",
                "provider": "expo",
            },
            headers=headers,
        )
        dev = r.json().get("device", {})
        check("register device", r.status_code == 201 and dev.get("platform") == "android", r.text)

        r = c.get(API + "/devices", headers=headers)
        check("list devices", r.status_code == 200 and len(r.json()["devices"]) >= 1, r.text)

        print("\n[billing + usage]")
        r = c.put(
            API + "/me/subscription",
            json={"plan_code": plan_code, "status": "active", "provider": "demo"},
            headers=headers,
        )
        check(
            "set subscription",
            r.status_code == 200 and r.json().get("plan", {}).get("code") == plan_code,
            r.text,
        )

        r = c.get(API + "/me/usage", headers=headers)
        check("usage report", r.status_code == 200 and "items" in r.json(), r.text)

        r = c.get(API + "/me/subscription", headers=headers)
        check(
            "subscription status",
            r.status_code == 200 and r.json().get("plan", {}).get("code") == plan_code,
            r.text,
        )

        print("\n[admin — system overview]")
        r = c.get(API + "/admin/system", headers=headers)
        check("admin system overview", r.status_code == 200, r.text)

        r = c.get(API + "/admin/users", headers=headers)
        users = r.json().get("users", r.json().get("items", []))
        check(
            "admin users list",
            r.status_code == 200 and any(u.get("email") == email for u in users),
            r.text,
        )

        r = c.get(API + "/admin/plans", headers=headers)
        check("admin plans list", r.status_code == 200 and len(r.json().get("items", [])) >= 1, r.text)

        print("\n[security — unauthorized access is rejected]")
        r = c.get(API + "/auth/me")
        check("unauthenticated me rejected", r.status_code == 401, f"status={r.status_code}")

        r = c.get(API + "/admin/users")
        check("unauthenticated admin rejected", r.status_code == 401, f"status={r.status_code}")

        r = c.get(API + "/watchlists")
        check("unauthenticated watchlists rejected", r.status_code == 401, f"status={r.status_code}")

    print("\n" + "=" * 46)
    print(f"E2E smoke test: {len(PASSED)} passed, {len(FAILED)} failed")
    if FAILED:
        print(f"Failed steps: {', '.join(FAILED)}")
        return 1
    print("ALL STEPS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
