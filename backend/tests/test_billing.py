"""Billing-provider abstraction tests (ADR-011, demo mode)."""

from sqlalchemy import select

from app.models import Payment, Subscription


def _register(client, email):
    return client.post(
        "/api/v1/auth/register", json={"email": email, "password": "password123"}
    ).json()


def _subscribe(client, token, plan_code="pro", provider="demo"):
    return client.put(
        "/api/v1/me/subscription",
        json={"plan_code": plan_code, "status": "active", "provider": provider},
        headers={"Authorization": f"Bearer {token}"},
    )


class TestBillingProvider:
    def test_demo_subscription_creates_zero_charge(self, client, db_session):
        _ = _register(client, "buyer@x.com")
        login = client.post(
            "/api/v1/auth/login", json={"email": "buyer@x.com", "password": "password123"}
        )
        token = login.json()["access_token"]
        resp = _subscribe(client, token, "pro", "demo")
        assert resp.status_code == 200
        assert resp.json()["provider"] == "demo"

        charge = db_session.execute(select(Payment).where(Payment.user_id == 1)).scalars().first()
        assert charge is not None
        assert charge.amount_cents == 0
        assert charge.provider == "demo"
        assert charge.status == "succeeded"

    def test_none_provider_records_no_payment(self, client, db_session):
        _ = _register(client, "free@x.com")
        login = client.post(
            "/api/v1/auth/login", json={"email": "free@x.com", "password": "password123"}
        )
        token = login.json()["access_token"]
        resp = _subscribe(client, token, "free", "none")
        assert resp.status_code == 200
        assert resp.json()["provider"] == "none"
        sub = db_session.execute(select(Subscription).where(Subscription.user_id == 1)).scalars().first()
        assert sub.payment_provider == "none"
        assert db_session.execute(select(Payment).where(Payment.user_id == 1)).scalars().first() is None

    def test_reassign_cancels_previous(self, client, db_session):
        _ = _register(client, "switcher@x.com")
        login = client.post(
            "/api/v1/auth/login", json={"email": "switcher@x.com", "password": "password123"}
        )
        token = login.json()["access_token"]
        assert _subscribe(client, token, "pro", "demo").status_code == 200
        assert _subscribe(client, token, "free", "demo").status_code == 200
        subs = db_session.execute(select(Subscription).where(Subscription.user_id == 1)).scalars().all()
        assert [s.status for s in subs].count("active") == 1
        assert sum(1 for s in subs if s.status == "canceled") == 1
