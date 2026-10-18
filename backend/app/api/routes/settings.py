"""Account settings: notification preferences + push device registration.

All endpoints are scoped to the authenticated user. Preferences upsert on
(user_id, category); devices upsert on (user_id, push_token).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Device, NotificationPreference, Plan, Subscription, User
from app.services.quotas import usage_report

router = APIRouter(tags=["settings"])

_CATEGORIES = {"general", "price_alerts", "scenario_alerts", "news_alerts"}
_PLATFORMS = {"android", "ios", "web"}
_PROVIDERS = {"expo", "log", "none"}


class PrefUpsert(BaseModel):
    category: str = Field(default="general")
    channel: str = Field(default="push")  # push | email | webhook | log
    enabled: bool = True


class DeviceRegister(BaseModel):
    platform: str = Field(default="web")
    push_token: str = Field(min_length=5, max_length=300)
    provider: str = Field(default="expo")


def _pref_snapshot(p: NotificationPreference) -> dict:
    return {
        "category": p.category,
        "channel": p.channel,
        "enabled": p.enabled,
    }


@router.get("/notification-preferences")
def get_preferences(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    rows = db.execute(
        select(NotificationPreference).where(NotificationPreference.user_id == user.id)
    ).scalars().all()
    by_category = {p.category: p for p in rows}
    # Return every known category so the UI can render all switches.
    return {
        "preferences": [
            _pref_snapshot(by_category.get(cat) or NotificationPreference(category=cat))
            for cat in sorted(_CATEGORIES)
        ]
    }


@router.put("/notification-preferences")
def upsert_preferences(
    payload: list[PrefUpsert],
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    for item in payload:
        if item.category not in _CATEGORIES:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                f"Unknown category '{item.category}'. Allowed: {sorted(_CATEGORIES)}",
            )
    for item in payload:
        row = db.execute(
            select(NotificationPreference).where(
                NotificationPreference.user_id == user.id,
                NotificationPreference.category == item.category,
            )
        ).scalar_one_or_none()
        if row is None:
            row = NotificationPreference(user_id=user.id, category=item.category)
            db.add(row)
        row.channel = item.channel
        row.enabled = item.enabled
    db.commit()
    return get_preferences(db, user)


@router.get("/devices")
def list_devices(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    rows = db.execute(
        select(Device).where(Device.user_id == user.id).order_by(Device.id.desc())
    ).scalars().all()
    return {
        "devices": [
            {
                "id": d.id,
                "platform": d.platform,
                "provider": d.provider,
                "push_token": f"{d.push_token[:6]}…{d.push_token[-4:]}",
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in rows
        ]
    }


@router.post("/devices", status_code=status.HTTP_201_CREATED)
def register_device(
    payload: DeviceRegister,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    if payload.platform not in _PLATFORMS:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Unknown platform. Allowed: {sorted(_PLATFORMS)}",
        )
    row = db.execute(
        select(Device).where(
            Device.user_id == user.id, Device.push_token == payload.push_token
        )
    ).scalar_one_or_none()
    if row is None:
        row = Device(
            user_id=user.id,
            platform=payload.platform,
            push_token=payload.push_token,
            provider=payload.provider,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
    return {"device": {"id": row.id, "platform": row.platform, "provider": row.provider}}


@router.delete("/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device(
    device_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    row = db.get(Device, device_id)
    if row is None or row.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Device not found")
    db.delete(row)
    db.commit()


# ---------------------------------------------------------------- plan & usage


class SubscriptionSet(BaseModel):
    plan_code: str
    status: str = "active"
    provider: str = "demo"


@router.get("/me/usage")
def my_usage(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    return usage_report(db, user)


@router.get("/me/subscription")
def my_subscription(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    report = usage_report(db, user)
    sub = db.execute(
        select(Subscription)
        .where(Subscription.user_id == user.id, Subscription.status == "active")
        .order_by(Subscription.id.desc())
        .limit(1)
    ).scalar_one_or_none()
    return {
        "plan": report["plan"],
        "provider": sub.payment_provider if sub else "none",
        "current_period_end": sub.current_period_end.isoformat() if sub and sub.current_period_end else None,
    }


@router.put("/me/subscription")
def set_subscription(
    payload: SubscriptionSet,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """Assign a plan to the current user (demo billing). Super-visible, self-serve."""
    plan = db.execute(select(Plan).where(Plan.code == payload.plan_code)).scalar_one_or_none()
    if plan is None or not plan.is_active or plan.is_archived:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Plan '{payload.plan_code}' not found")
    # cancel old active subs
    for old in db.execute(
        select(Subscription).where(Subscription.user_id == user.id, Subscription.status == "active")
    ).scalars().all():
        old.status = "canceled"
    sub = Subscription(
        user_id=user.id,
        plan_id=plan.id,
        status=payload.status,
        payment_provider=payload.provider,
    )
    db.add(sub)
    db.commit()
    return {"plan": {"code": plan.code, "name": plan.name}, "status": sub.status}
