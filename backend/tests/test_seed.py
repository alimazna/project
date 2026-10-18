"""Plan seeding idempotence test."""

from sqlalchemy import func, select

from app.models import Plan
from app.services.seed import seed_plans


def test_seed_creates_default_plans(db_session):
    created = seed_plans(db_session)
    assert created == 2  # free + pro
    count = db_session.execute(select(func.count()).select_from(Plan)).scalar_one()
    assert count == 2


def test_seed_is_idempotent(db_session):
    assert seed_plans(db_session) == 2
    assert seed_plans(db_session) == 0
    count = db_session.execute(select(func.count()).select_from(Plan)).scalar_one()
    assert count == 2


def test_public_plans_expose_seeded_codes(client, db_session):
    seed_plans(db_session)
    codes = {p["code"] for p in client.get("/api/v1/plans").json()["items"]}
    assert {"free", "pro"} <= codes
