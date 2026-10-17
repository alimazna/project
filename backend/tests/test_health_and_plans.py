"""API smoke/health/plans tests."""

from app.models import Plan


def test_healthz(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_root(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "docs" in resp.json()


def test_public_plans_empty(client):
    resp = client.get("/api/v1/plans")
    assert resp.status_code == 200
    assert resp.json()["items"] == []


def test_public_plans_from_db(client, db_session):
    db_session.add(
        Plan(code="free", name="Free", display_price="$0", is_active=True, sort_order=1)
    )
    db_session.commit()
    resp = client.get("/api/v1/plans")
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["code"] == "free"


def test_inactive_plan_hidden(client, db_session):
    db_session.add(
        Plan(code="legacy", name="Legacy", display_price="$9", is_active=False)
    )
    db_session.commit()
    resp = client.get("/api/v1/plans")
    assert resp.json()["total"] == 0
