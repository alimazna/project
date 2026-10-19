"""Pytest fixtures: isolated in-memory DB per test."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.ratelimit import reset_rate_limits
from app.db.session import Base, get_db
from app.main import app
from app.services.seed import seed_plans, seed_symbols


@pytest.fixture(autouse=True)
def _clean_rate_limits():
    reset_rate_limits()
    yield
    reset_rate_limits()


@pytest.fixture()
def engine_factory():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    db = Session()
    seed_plans(db)
    seed_symbols(db)
    db.close()
    return engine


@pytest.fixture()
def db_session(engine_factory):
    SessionTesting = sessionmaker(bind=engine_factory, autoflush=False, expire_on_commit=False)
    session = SessionTesting()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(engine_factory):
    SessionTesting = sessionmaker(bind=engine_factory, autoflush=False, expire_on_commit=False)

    def override_get_db():
        db = SessionTesting()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
