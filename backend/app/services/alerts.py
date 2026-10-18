"""Alert evaluation service.

Checks every active alert against the latest known state (ticker/candle for
price alerts, last scenario for scenario alerts, most relevant article for
news alerts). Fired alerts record an ``AlertDelivery`` row and stamp
``last_fired_at`` for cooldown dedup.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Alert,
    AlertDelivery,
    Candle,
    NewsArticle,
    Scenario,
    Ticker,
)
from app.models import User as UserModel

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(UTC)


def _as_utc(dt: datetime | None) -> datetime | None:
    """SQLite returns naive datetimes; normalize to aware UTC before comparing."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def latest_price(db: Session, symbol: str) -> float | None:
    ticker = db.execute(
        select(Ticker).where(Ticker.symbol == symbol).order_by(Ticker.fetched_at.desc()).limit(1)
    ).scalar_one_or_none()
    if ticker is not None:
        return ticker.last_price
    candle = db.execute(
        select(Candle).where(Candle.symbol == symbol).order_by(Candle.open_time.desc()).limit(1)
    ).scalar_one_or_none()
    return candle.close if candle is not None else None


def latest_scenario(db: Session, symbol: str) -> Scenario | None:
    return db.execute(
        select(Scenario).where(Scenario.symbol == symbol).order_by(Scenario.created_at.desc()).limit(1)
    ).scalar_one_or_none()


def latest_news(db: Session, symbol: str) -> NewsArticle | None:
    return db.execute(
        select(NewsArticle)
        .where(NewsArticle.assets.like(f'%"{symbol}"%'))
        .order_by(NewsArticle.published_at.desc().nullslast(), NewsArticle.id.desc())
        .limit(1)
    ).scalar_one_or_none()


def _mine_cooldown_dt(alert: Alert) -> datetime:
    return _now() - timedelta(minutes=alert.cooldown_minutes or 0)


def _recently_fired(alert: Alert) -> bool:
    last = _as_utc(alert.last_fired_at)
    if last is None:
        return False
    return last > _mine_cooldown_dt(alert)


def _minute_dedup_key(alert: Alert) -> str:
    return f"{alert.id}:{alert.kind}:{int(_now().timestamp() // 60)}"


def _already_delivered_this_minute(db: Session, alert: Alert) -> bool:
    key = _minute_dedup_key(alert)
    row = db.execute(
        select(AlertDelivery.id)
        .where(AlertDelivery.alert_id == alert.id, AlertDelivery.dedup_key == key)
        .limit(1)
    ).scalar_one_or_none()
    return row is not None


def evaluate_alert(db: Session, alert: Alert) -> AlertDelivery | None:
    """Return an AlertDelivery if the alert fires right now, else None."""
    if not alert.is_active:
        return None
    if _recently_fired(alert) or _already_delivered_this_minute(db, alert):
        return None

    price = latest_price(db, alert.symbol)
    trigger_fired = False
    detail: dict = {}

    if alert.kind == "price_above" and price is not None and alert.value is not None:
        trigger_fired = price >= alert.value
        detail = {"price": price, "threshold": alert.value}
    elif alert.kind == "price_below" and price is not None and alert.value is not None:
        trigger_fired = price <= alert.value
        detail = {"price": price, "threshold": alert.value}
    elif alert.kind in ("scenario_bullish", "scenario_bearish"):
        scen = latest_scenario(db, alert.symbol)
        want = "BULLISH" if alert.kind == "scenario_bullish" else "BEARISH"
        if scen is not None:
            trigger_fired = scen.direction == want
            detail = {"direction": scen.direction, "scenario_id": scen.id}
    elif alert.kind == "news_relevance":
        article = latest_news(db, alert.symbol)
        if article is not None:
            trigger_fired = (article.relevance_score or 0) >= 0.6
            detail = {"article_id": article.id, "relevance": article.relevance_score}

    if not trigger_fired:
        return None

    now = _now()
    dedup_key = _minute_dedup_key(alert)
    delivery = AlertDelivery(
        alert_id=alert.id,
        user_id=alert.user_id,
        channel="log",
        status="attempted",
        dedup_key=dedup_key,
    )
    alert.last_fired_at = now
    db.add(alert)
    db.add(delivery)
    db.commit()
    logger.info("alert %s fired for %s (%s): %s", alert.id, alert.symbol, alert.kind, detail)
    return delivery


def evaluate_user_alerts(db: Session, user: UserModel) -> dict:
    alerts = db.execute(
        select(Alert).where(Alert.user_id == user.id, Alert.is_active.is_(True))
    ).scalars().all()
    fired = 0
    for alert in alerts:
        if evaluate_alert(db, alert) is not None:
            fired += 1
    return {"evaluated": len(alerts), "fired": fired}


def evaluate_all(db: Session) -> dict:
    alerts = db.execute(select(Alert).where(Alert.is_active.is_(True))).scalars().all()
    fired = 0
    evaluated = 0
    for alert in alerts:
        if evaluate_alert(db, alert) is not None:
            fired += 1
        evaluated += 1
    return {"evaluated": evaluated, "fired": fired}
