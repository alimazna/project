"""Idempotent plan seeding for fresh databases."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Plan

DEFAULT_PLANS = [
    {
        "code": "free",
        "name": "Free",
        "description": "Perpetual free tier for casual explorers.",
        "display_price": "$0",
        "billing_interval": "none",
        "currency": "USD",
        "sort_order": 0,
        "is_active": True,
        "features": [
            "3 watchlists",
            "5 active alerts",
            "Daily news digest",
            "1-hour charts",
        ],
        "quotas": {"watchlists": 3, "alerts": 5, "scenarios_per_day": 5},
    },
    {
        "code": "pro",
        "name": "Pro",
        "description": "For active traders — more watchlists, alerts and scenarios.",
        "display_price": "$19",
        "billing_interval": "monthly",
        "currency": "USD",
        "sort_order": 1,
        "is_active": True,
        "features": [
            "Unlimited watchlists",
            "50 active alerts",
            "Real-time news & scenario alerts",
            "All timeframes + advanced charts",
            "Push notifications (mobile)",
        ],
        "quotas": {"watchlists": 50, "alerts": 50, "scenarios_per_day": 50},
    },
]


def seed_plans(db: Session) -> int:
    """Insert default plans if none exist. Returns how many were created."""
    existing = db.execute(select(Plan.code)).scalars().all()
    known = set(existing)
    created = 0
    for data in DEFAULT_PLANS:
        if data["code"] in known:
            continue
        db.add(Plan(**data))
        created += 1
    if created:
        db.commit()
    return created
