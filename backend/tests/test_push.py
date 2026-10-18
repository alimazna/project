"""Push-provider abstraction tests (ADR-012): provider selection, delivery
attempts against registered devices, and alert→push integration.
"""

from sqlalchemy import select

from app.models import Alert, AlertDelivery, User
from app.providers.base import TickerData
from app.services.ingestion import upsert_ticker
from app.services.push import (
    LogOnlyPushProvider,
    PushError,
    alert_delivery_message,
    get_push_provider,
    notify_user,
)


def _auth(client, email: str = "push@b.com") -> str:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "display_name": "P"},
    )
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})
    return login.json()["access_token"]


class TestProviderSelection:
    def test_log_provider_is_default(self):
        provider = get_push_provider()
        assert isinstance(provider, LogOnlyPushProvider)
        assert provider.label == "log"

    def test_unknown_provider_raises(self):
        try:
            get_push_provider("bogus")
        except PushError:
            pass
        else:  # pragma: no cover
            raise AssertionError("expected PushError for unknown provider")

    def test_log_provider_never_claims_delivery(self):
        result = LogOnlyPushProvider().send(token="ExponentPushToken[abc]", title="T", body="B")
        assert result["provider"] == "log"
        assert result["delivered"] is False
        assert result["status"] == "attempted"


class TestAlertDeliveryMessage:
    def test_price_above(self):
        a = Alert(symbol="BTC/USD", kind="price_above", value=60000)
        title, body = alert_delivery_message(a, {"threshold": 60000})
        assert "BTC/USD" in title
        assert "60000" in body

    def test_scenario_message(self):
        a = Alert(symbol="ETH/USD", kind="scenario_bullish")
        title, body = alert_delivery_message(a, {"direction": "BULLISH"})
        assert "BULLISH" in title


class TestNotifyUser:
    def test_no_devices_records_explicit_skip(self, db_session):
        user = User(email="x@b.com", password_hash="h", display_name="X")
        db_session.add(user)
        db_session.commit()
        results = notify_user(db_session, user_id=user.id, title="T", body="B")
        assert results == [{"devices": 0, "status": "skipped", "reason": "no_registered_devices"}]

    def test_log_delivery_to_registered_device(self, client, db_session):
        token = _auth(client)
        headers = {"Authorization": f"Bearer {token}"}
        client.post(
            "/api/v1/devices",
            json={"platform": "android", "push_token": "ExponentPushToken[abc123]", "provider": "expo"},
            headers=headers,
        )

        user = db_session.execute(select(User)).scalars().first()
        results = notify_user(db_session, user_id=user.id, title="T", body="B")
        assert results and results[0]["provider"] == "log"
        assert results[0]["status"] == "attempted"

        # no alert_id → delivery row is written by the calling alert flow only;
        # notify_user alone must not fabricate an alert-attached record.
        deliveries = db_session.query(AlertDelivery).filter_by(user_id=user.id).all()
        assert deliveries == []

    def test_alert_fire_dispatches_push_and_records_delivery(self, client, db_session):
        token = _auth(client)
        headers = {"Authorization": f"Bearer {token}"}
        client.post(
            "/api/v1/devices",
            json={"platform": "ios", "push_token": "ExponentPushToken[xyz789]", "provider": "expo"},
            headers=headers,
        )
        upsert_ticker(db_session, TickerData("BTC/USD", 61000.0))

        alert = client.post(
            "/api/v1/alerts",
            json={"symbol": "BTC/USD", "kind": "price_above", "value": 60000, "cooldown_minutes": 0},
            headers=headers,
        ).json()["alert"]
        evaluate = client.post(f"/api/v1/alerts/{alert['id']}/evaluate", headers=headers)
        assert evaluate.json()["fired"] is True

        deliveries = db_session.query(AlertDelivery).filter_by(alert_id=alert["id"]).all()
        channels = {d.channel for d in deliveries}
        assert {"log", "push"} <= channels
        # the push row is recorded as attempted (log-only — honest label)
        push_rows = [d for d in deliveries if d.channel == "push"]
        assert push_rows and push_rows[0].status == "attempted"
        assert push_rows[0].error is None
