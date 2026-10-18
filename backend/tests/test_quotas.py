"""Quota enforcement + plan assignment tests."""

from app.services.seed import seed_plans


def _auth(client, email: str = "q@x.com") -> str:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "display_name": "Q"},
    )
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})
    return login.json()["access_token"]


def _headers(token: str):
    return {"Authorization": f"Bearer {token}"}


class TestUsage:
    def test_usage_endpoint_defaults_to_free(self, client, db_session):
        seed_plans(db_session)
        token = _auth(client)
        resp = client.get("/api/v1/me/usage", headers=_headers(token))
        assert resp.status_code == 200
        body = resp.json()
        assert body["plan"]["code"] == "free"
        by_key = {i["key"]: i for i in body["items"]}
        assert by_key["watchlists"]["limit"] == 3
        assert by_key["alerts"]["limit"] == 5

    def test_upgrade_bumps_limits(self, client, db_session):
        seed_plans(db_session)
        token = _auth(client)
        put = client.put(
            "/api/v1/me/subscription", json={"plan_code": "pro"}, headers=_headers(token)
        )
        assert put.status_code == 200
        usage = client.get("/api/v1/me/usage", headers=_headers(token)).json()
        by_key = {i["key"]: i for i in usage["items"]}
        assert usage["plan"]["code"] == "pro"
        assert by_key["watchlists"]["limit"] == 50
        assert by_key["alerts"]["limit"] == 50


class TestEnforcement:
    def test_free_plan_caps_watchlists(self, client, db_session):
        seed_plans(db_session)
        token = _auth(client)
        h = _headers(token)
        free_quota = 3
        for _ in range(free_quota):
            created = client.post(
                "/api/v1/watchlists", json={"name": "WL", "symbols": []}, headers=h
            )
            assert created.status_code == 201
        blocked = client.post("/api/v1/watchlists", json={"name": "Too many", "symbols": []}, headers=h)
        assert blocked.status_code == 403
        assert "watchlists" in blocked.json()["detail"]

    def test_upgraded_plan_allows_more_watchlists(self, client, db_session):
        seed_plans(db_session)
        token = _auth(client)
        h = _headers(token)
        client.put("/api/v1/me/subscription", json={"plan_code": "pro"}, headers=h)
        pro_quota = 50
        # sanity: still capped somewhere high; create 5 fine
        for i in range(5):
            resp = client.post(
                "/api/v1/watchlists", json={"name": f"WL{i}", "symbols": []}, headers=h
            )
            assert resp.status_code == 201
        assert client.get("/api/v1/me/usage", headers=h).json()["items"][0]["limit"] == pro_quota

    def test_free_plan_caps_alerts(self, client, db_session):
        seed_plans(db_session)
        token = _auth(client)
        h = _headers(token)
        free_quota = 5
        for _ in range(free_quota):
            resp = client.post(
                "/api/v1/alerts",
                json={"symbol": "BTC/USD", "kind": "price_above", "value": 1},
                headers=h,
            )
            assert resp.status_code == 201
        blocked = client.post(
            "/api/v1/alerts",
            json={"symbol": "BTC/USD", "kind": "price_above", "value": 1},
            headers=h,
        )
        assert blocked.status_code == 403

    def test_subscription_unknown_plan(self, client, db_session):
        seed_plans(db_session)
        token = _auth(client)
        resp = client.put(
            "/api/v1/me/subscription", json={"plan_code": "nonexistent"}, headers=_headers(token)
        )
        assert resp.status_code == 404
