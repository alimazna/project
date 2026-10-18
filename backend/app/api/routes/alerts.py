"""User alerts — authenticated CRUD scoped to the current user.

Kinds: price_above | price_below | scenario_bullish | scenario_bearish |
news_relevance. Firing is evaluated on-demand here and in the ingestion loop
(``app.services.alerts.evaluate_all``).
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Alert, AlertDelivery, User
from app.services.alerts import evaluate_alert

router = APIRouter(prefix="/alerts", tags=["alerts"])

_ALERT_KINDS = {"price_above", "price_below", "scenario_bullish", "scenario_bearish", "news_relevance"}


class AlertCreate(BaseModel):
    symbol: str = Field(min_length=1, max_length=30)
    kind: str
    value: float | None = Field(default=None, ge=0)
    cooldown_minutes: int = Field(default=30, ge=0, le=1440)


class AlertUpdate(BaseModel):
    is_active: bool | None = None
    value: float | None = Field(default=None, ge=0)
    cooldown_minutes: int | None = Field(default=None, ge=0, le=1440)
    symbol: str | None = Field(default=None, min_length=1, max_length=30)


def _snapshot(a: Alert) -> dict:
    return {
        "id": a.id,
        "symbol": a.symbol,
        "kind": a.kind,
        "value": a.value,
        "is_active": a.is_active,
        "cooldown_minutes": a.cooldown_minutes,
        "last_fired_at": _iso(a.last_fired_at),
        "created_at": _iso(a.created_at),
    }


def _iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.isoformat()


def _owned(db: Session, user: User, alert_id: int) -> Alert:
    row = db.get(Alert, alert_id)
    if row is None or row.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Alert not found")
    return row


def _validate_kind(kind: str) -> str:
    if kind not in _ALERT_KINDS:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Unknown alert kind. Allowed: {sorted(_ALERT_KINDS)}",
        )
    return kind


@router.get("/deliveries")
def list_deliveries(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
) -> dict:
    rows = db.execute(
        select(AlertDelivery)
        .where(AlertDelivery.user_id == user.id)
        .order_by(AlertDelivery.id.desc())
        .limit(limit)
    ).scalars().all()
    return {
        "deliveries": [
            {
                "id": d.id,
                "alert_id": d.alert_id,
                "symbol": (db.get(Alert, d.alert_id).symbol if db.get(Alert, d.alert_id) else None),
                "channel": d.channel,
                "status": d.status,
                "created_at": _iso(d.created_at),
            }
            for d in rows
        ]
    }


@router.get("/{alert_id}")
def get_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    return {"alert": _snapshot(_owned(db, user, alert_id))}


@router.get("")
def list_alerts(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    active: bool | None = Query(None),
) -> dict:
    q = select(Alert).where(Alert.user_id == user.id).order_by(Alert.id.desc())
    if active is not None:
        q = q.where(Alert.is_active == active)
    rows = db.execute(q).scalars().all()
    return {"alerts": [_snapshot(a) for a in rows]}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_alert(
    payload: AlertCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    _validate_kind(payload.kind)
    if payload.value is None and payload.kind in ("price_above", "price_below"):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Price alerts need a value")
    row = Alert(
        user_id=user.id,
        symbol=payload.symbol.upper(),
        kind=payload.kind,
        value=payload.value,
        cooldown_minutes=payload.cooldown_minutes,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"alert": _snapshot(row)}


@router.put("/{alert_id}")
def update_alert(
    alert_id: int,
    payload: AlertUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    row = _owned(db, user, alert_id)
    if payload.is_active is not None:
        row.is_active = payload.is_active
    if payload.value is not None:
        row.value = payload.value
    if payload.cooldown_minutes is not None:
        row.cooldown_minutes = payload.cooldown_minutes
    if payload.symbol is not None:
        row.symbol = payload.symbol.upper()
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"alert": _snapshot(row)}


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    row = _owned(db, user, alert_id)
    db.delete(row)
    db.commit()


@router.post("/{alert_id}/evaluate")
def evaluate_now(
    alert_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    row = _owned(db, user, alert_id)
    delivery = evaluate_alert(db, row)
    return {"fired": delivery is not None, "evaluated": True}
