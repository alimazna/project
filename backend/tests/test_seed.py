"""Plan seeding idempotence test."""

from sqlalchemy import func, select

from app.models import Plan
from app.services.seed import seed_plans


def test_seed_is_idempotent(db_session):
    # plans are pre-seeded by the engine_factory fixture
    assert seed_plans(db_session) == 0
    assert seed_plans(db_session) == 0
    count = db_session.execute(select(func.count()).select_from(Plan)).scalar_one()
    assert count == 2


def test_public_plans_expose_seeded_codes(client):
    codes = {p["code"] for p in client.get("/api/v1/plans").json()["items"]}
    assert {"free", "pro"} <= codes


def test_seed_on_empty_db_fresh_counts(db_session):
    from sqlalchemy import delete

    db_session.execute(delete(Plan))
    db_session.commit()
    assert seed_plans(db_session) == 2
