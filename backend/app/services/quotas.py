"""Quota enforcement.

Every authenticated user maps to a plan: the latest active subscription wins,
otherwise the ``free`` plan is the default. ``require_quota`` is used as a
FastAPI dependency on create endpoints to fail fast with a 403 that carries the
quota key, limit and current usage.
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Alert, Plan, Subscription, User, Watchlist
from app.services.seed import DEFAULT_PLANS

DEFAULT_FREE_QUOTAS = next((p["quotas"] for p in DEFAULT_PLANS if p["code"] == "free"), {})


def _active_subscription(db: Session, user: User) -> Subscription | None:
    now = datetime.now(UTC)
    return db.execute(
        select(Subscription)
        .where(
            Subscription.user_id == user.id,
            Subscription.status == "active",
            (Subscription.current_period_end.is_(None)) | (Subscription.current_period_end > now),
        )
        .order_by(Subscription.id.desc())
        .limit(1)
    ).scalar_one_or_none()


def effective_plan(db: Session, user: User) -> Plan:
    sub = _active_subscription(db, user)
    if sub is not None:
        plan = db.get(Plan, sub.plan_id)
        if plan is not None and plan.is_active and not plan.is_archived:
            return plan
    free = db.execute(select(Plan).where(Plan.code == "free")).scalar_one_or_none()
    if free is not None:
        return free
    # Fall back to the code-level default if the DB has no seeded plan yet.
    return Plan(quotas=DEFAULT_FREE_QUOTAS.copy(), code="free", name="Free")


def plan_quotas(db: Session, user: User) -> dict:
    plan = effective_plan(db, user)
    return dict(plan.quotas or {})


def usage_counts(db: Session, user: User) -> dict:
    watchlists = db.execute(
        select(func.count()).select_from(Watchlist).where(Watchlist.user_id == user.id)
    ).scalar_one()
    alerts = db.execute(
        select(func.count()).select_from(Alert).where(Alert.user_id == user.id)
    ).scalar_one()
    return {"watchlists": watchlists, "alerts": alerts}


def usage_report(db: Session, user: User) -> dict:
    quotas = plan_quotas(db, user)
    used = usage_counts(db, user)
    items = []
    for key in ("watchlists", "alerts", "scenarios_per_day"):
        limit = quotas.get(key)
        current = used.get(key, 0)
        items.append(
            {
                "key": key,
                "used": current,
                "limit": limit,
                "remaining": None if limit is None else max(0, int(limit) - int(current)),
            }
        )
    plan = effective_plan(db, user)
    return {
        "plan": {"code": plan.code, "name": plan.name},
        "items": items,
    }


def enforce_quota(db: Session, user: User, key: str) -> None:
    quotas = plan_quotas(db, user)
    limit = quotas.get(key)
    if limit is None:
        return  # unlimited
    current = usage_counts(db, user).get(key, 0)
    if int(current) >= int(limit):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            f"Quota exceeded for '{key}': {current}/{limit}",
            headers={"X-Quota-Key": key, "X-Quota-Limit": str(limit), "X-Quota-Used": str(current)},
        )


def require_quota(key: str):
    def check(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> User:
        enforce_quota(db, user, key)
        return user

    return check
