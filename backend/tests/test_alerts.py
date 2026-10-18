"""Alerts API tests: CRUD, validation, evaluation, delivery log, isolation."""

from app.models import Alert
from app.providers.base import TickerData
from app.services.ingestion import upsert_ticker


def _auth(client, email: str = "al@b.com") -> str:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "display_name": "A"},
    )
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})
    return login.json()["access_token"]


class TestAlertCRUD:
    def test_requires_auth(self, client):
        assert client.get("/api/v1/alerts").status_code == 401

    def test_create_price_alert(self, client):
        token = _auth(client)
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.post(
            "/api/v1/alerts",
            json={"symbol": "btc/usd", "kind": "price_above", "value": 50000},
            headers=headers,
        )
        assert resp.status_code == 201
        alert = resp.json()["alert"]
        assert alert["symbol"] == "BTC/USD"
        assert alert["kind"] == "price_above"
        assert alert["value"] == 50000
        assert alert["is_active"] is True

    def test_price_alert_needs_value(self, client):
        token = _auth(client)
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.post(
            "/api/v1/alerts", json={"symbol": "BTC/USD", "kind": "price_above"}, headers=headers
        )
        assert resp.status_code == 422

    def test_unknown_kind_rejected(self, client):
        token = _auth(client)
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.post(
            "/api/v1/alerts", json={"symbol": "BTC/USD", "kind": "moon_alert"}, headers=headers
        )
        assert resp.status_code == 422

    def test_update_delete(self, client):
        token = _auth(client)
        headers = {"Authorization": f"Bearer {token}"}
        alert = client.post(
            "/api/v1/alerts",
            json={"symbol": "BTC/USD", "kind": "price_below", "value": 1000},
            headers=headers,
        ).json()["alert"]

        upd = client.put(
            f"/api/v1/alerts/{alert['id']}",
            json={"is_active": False},
            headers=headers,
        )
        assert upd.json()["alert"]["is_active"] is False

        assert client.delete(f"/api/v1/alerts/{alert['id']}", headers=headers).status_code == 204

    def test_isolation(self, client, db_session):
        a_token = _auth(client, "u1@b.com")
        b_token = _auth(client, "u2@b.com")
        h_a = {"Authorization": f"Bearer {a_token}"}
        h_b = {"Authorization": f"Bearer {b_token}"}
        alert = client.post(
            "/api/v1/alerts",
            json={"symbol": "BTC/USD", "kind": "price_above", "value": 1},
            headers=h_a,
        ).json()["alert"]
        assert client.get(f"/api/v1/alerts/{alert['id']}", headers=h_b).status_code in (401, 404)
        assert client.delete(f"/api/v1/alerts/{alert['id']}", headers=h_b).status_code in (401, 404)

    def test_get_single_returns_404(self, client):
        token = _auth(client)
        headers = {"Authorization": f"Bearer {token}"}
        assert client.get("/api/v1/alerts/9999", headers=headers).status_code == 404


class TestEvaluate:
    def test_price_alert_fires(self, client, db_session):
        token = _auth(client)
        headers = {"Authorization": f"Bearer {token}"}
        upsert_ticker(db_session, TickerData("BTC/USD", 61000.0))

        alert = client.post(
            "/api/v1/alerts",
            json={"symbol": "BTC/USD", "kind": "price_above", "value": 60000, "cooldown_minutes": 0},
            headers=headers,
        ).json()["alert"]

        evaluate = client.post(f"/api/v1/alerts/{alert['id']}/evaluate", headers=headers)
        assert evaluate.status_code == 200
        assert evaluate.json()["fired"] is True

        # cooldown 0 → but last_fired stamped: second call in same minute dedupes
        second = client.post(f"/api/v1/alerts/{alert['id']}/evaluate", headers=headers)
        assert second.json()["fired"] is False

        deliveries = client.get("/api/v1/alerts/deliveries", headers=headers)
        assert len(deliveries.json()["deliveries"]) >= 1

    def test_price_alert_does_not_fire_below(self, client, db_session):
        token = _auth(client)
        headers = {"Authorization": f"Bearer {token}"}
        upsert_ticker(db_session, TickerData("BTC/USD", 40000.0))
        alert = client.post(
            "/api/v1/alerts",
            json={"symbol": "BTC/USD", "kind": "price_above", "value": 60000},
            headers=headers,
        ).json()["alert"]
        evaluate = client.post(f"/api/v1/alerts/{alert['id']}/evaluate", headers=headers)
        assert evaluate.json()["fired"] is False
        assert db_session.query(Alert).filter_by(id=alert["id"]).first().last_fired_at is None
