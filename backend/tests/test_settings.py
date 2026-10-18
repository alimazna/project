"""Notification preferences + device registration tests."""


def _auth(client, email: str = "st@b.com") -> str:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "display_name": "S"},
    )
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})
    return login.json()["access_token"]


class TestPreferences:
    def test_requires_auth(self, client):
        assert client.get("/api/v1/notification-preferences").status_code == 401

    def test_defaults_all_categories(self, client):
        token = _auth(client)
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.get("/api/v1/notification-preferences", headers=headers)
        assert resp.status_code == 200
        cats = {p["category"] for p in resp.json()["preferences"]}
        assert {"general", "price_alerts", "scenario_alerts", "news_alerts"} <= cats

    def test_upsert_persists(self, client):
        token = _auth(client)
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.put(
            "/api/v1/notification-preferences",
            json=[{"category": "price_alerts", "channel": "push", "enabled": False}],
            headers=headers,
        )
        assert resp.status_code == 200
        prefs = {p["category"]: p for p in resp.json()["preferences"]}
        assert prefs["price_alerts"]["enabled"] is False

        # fetch again — persisted
        again = client.get("/api/v1/notification-preferences", headers=headers)
        prefs2 = {p["category"]: p for p in again.json()["preferences"]}
        assert prefs2["price_alerts"]["enabled"] is False

    def test_invalid_category_rejected(self, client):
        token = _auth(client)
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.put(
            "/api/v1/notification-preferences",
            json=[{"category": "bogus", "channel": "push", "enabled": True}],
            headers=headers,
        )
        assert resp.status_code == 422


class TestDevices:
    def test_register_and_list(self, client):
        token = _auth(client)
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.post(
            "/api/v1/devices",
            json={"platform": "android", "push_token": "ExponentPushToken[abc123def]"},
            headers=headers,
        )
        assert resp.status_code == 201
        device_id = resp.json()["device"]["id"]

        listing = client.get("/api/v1/devices", headers=headers)
        assert len(listing.json()["devices"]) == 1
        # token is masked, not leaked in plaintext
        assert "abc123def" not in listing.json()["devices"][0]["push_token"]

        assert (
            client.delete(f"/api/v1/devices/{device_id}", headers=headers).status_code == 204
        )
        assert client.get("/api/v1/devices", headers=headers).json()["devices"] == []

    def test_duplicate_registration_is_idempotent(self, client):
        token = _auth(client)
        headers = {"Authorization": f"Bearer {token}"}
        payload = {"platform": "ios", "push_token": "ExponentPushToken[xyz]}", "provider": "expo"}
        first = client.post("/api/v1/devices", json=payload, headers=headers).status_code
        second = client.post("/api/v1/devices", json=payload, headers=headers).status_code
        assert first == second == 201
        assert len(client.get("/api/v1/devices", headers=headers).json()["devices"]) == 1

    def test_requires_auth(self, client):
        assert client.post("/api/v1/devices", json={"platform": "web", "push_token": "x" * 10}).status_code == 401
