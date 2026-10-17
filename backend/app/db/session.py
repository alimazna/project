"""SQLAlchemy engine and session factory.

Default engine is SQLite in WAL mode (zero-config, $0). PostgreSQL works by
setting DATABASE_URL (e.g. postgresql+psycopg://...) — models are portable.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

_engine_kwargs: dict = {"pool_pre_ping": True}

if settings.database_url.startswith("sqlite"):
    _engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(settings.database_url, **_engine_kwargs)


def init_engine(db_url: str | None = None):
    """Allow tests to rebind the global engine (e.g. in-memory SQLite)."""
    global engine
    if db_url and db_url != settings.database_url:
        kwargs: dict = {"pool_pre_ping": True}
        if db_url.startswith("sqlite"):
            kwargs["connect_args"] = {"check_same_thread": False}
        engine = create_engine(db_url, **kwargs)
    # Enable WAL for SQLite on every connect
    if str(engine.url).startswith("sqlite"):
        with engine.connect() as conn:
            conn.exec_driver_sql("PRAGMA journal_mode=WAL")
            conn.exec_driver_sql("PRAGMA foreign_keys=ON")
    return engine


class Base(DeclarativeBase):
    pass


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
