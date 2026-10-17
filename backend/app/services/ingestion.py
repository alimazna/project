"""Persistence layer for market data and news ingestion.

Persists provider-normalized data into the SQLAlchemy models: symbols,
candles (upsert by unique key), tickers, news articles (dedupe by URL),
and provider health.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, tuple_
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.models import (
    Candle,
    NewsArticle,
    NewsAsset,
    ProviderHealth,
    Symbol,
    Ticker,
)
from app.providers.base import CandleData, TickerData

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(UTC)


# ------------------------------------------------------------------ symbols

def ensure_symbols(db: Session, symbols: list[dict]) -> None:
    """Upsert symbol rows (primary key = symbol)."""
    for s in symbols:
        existing = db.get(Symbol, s["symbol"])
        if existing:
            existing.display_name = s.get("display_name") or existing.display_name
            existing.base = s.get("base") or existing.base
            existing.quote = s.get("quote") or existing.quote
        else:
            db.add(
                Symbol(
                    symbol=s["symbol"],
                    base=s.get("base") or "?",
                    quote=s.get("quote") or "USD",
                    display_name=s.get("display_name"),
                    provider=s.get("provider", "kraken"),
                )
            )
    db.commit()


# ------------------------------------------------------------------ candles

def upsert_candles(db: Session, candles: list[CandleData]) -> int:
    """Upsert candles on (symbol, interval, open_time). Returns inserted count.

    SQLite's ON CONFLICT rowcount includes both inserted and updated rows, so
    we pre-check which keys already exist to report true new inserts.
    """
    if not candles:
        return 0

    keys = [(c.symbol, c.interval, c.open_time) for c in candles]
    # Count how many batch keys already exist (row updated, not inserted).
    # SQLite returns naive datetimes; normalize to aware UTC for comparison.
    existing = {
        (sym, interval, _normalize_aware(ts))
        for sym, interval, ts in db.execute(
            select(Candle.symbol, Candle.interval, Candle.open_time).where(
                tuple_(Candle.symbol, Candle.interval, Candle.open_time).in_(keys)
            )
        ).all()
    }
    inserted = sum(1 for k in keys if k not in existing)

    for c in candles:
        close_time = c.open_time + _interval_delta(c.interval)
        stmt = sqlite_insert(Candle).values(
            symbol=c.symbol,
            interval=c.interval,
            open_time=c.open_time,
            close_time=close_time,
            open=c.open,
            high=c.high,
            low=c.low,
            close=c.close,
            volume=c.volume,
            closed=True,
            source="provider",
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["symbol", "interval", "open_time"],
            set_={
                "open": c.open,
                "high": c.high,
                "low": c.low,
                "close": c.close,
                "volume": c.volume,
                "close_time": close_time,
                "closed": True,
            },
        )
        db.execute(stmt)
    db.commit()
    return inserted


def _interval_delta(interval: str) -> timedelta:
    if interval.endswith("m"):
        return timedelta(minutes=int(interval[:-1]))
    if interval.endswith("h"):
        return timedelta(hours=int(interval[:-1]))
    if interval.endswith("d"):
        return timedelta(days=int(interval[:-1]))
    if interval.endswith("w"):
        return timedelta(weeks=int(interval[:-1]))
    return timedelta(hours=1)


def latest_candle_time(db: Session, symbol: str, interval: str) -> datetime | None:
    row = db.execute(
        select(Candle.close_time)
        .where(Candle.symbol == symbol, Candle.interval == interval)
        .order_by(Candle.close_time.desc())
        .limit(1)
    ).scalar_one_or_none()
    return _normalize_aware(row) if row is not None else None


def _normalize_aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


# ------------------------------------------------------------------ tickers

def upsert_ticker(db: Session, ticker: TickerData) -> None:
    db.add(
        Ticker(
            symbol=ticker.symbol,
            last_price=ticker.last_price,
            high_24h=ticker.high_24h,
            low_24h=ticker.low_24h,
            volume_24h=ticker.volume_24h,
            quote_volume_24h=ticker.quote_volume_24h,
            change_24h_pct=ticker.change_24h_pct,
        )
    )
    db.commit()


def latest_ticker(db: Session, symbol: str) -> Ticker | None:
    row = db.execute(
        select(Ticker).where(Ticker.symbol == symbol).order_by(Ticker.fetched_at.desc()).limit(1)
    ).scalar_one_or_none()
    return row


# ------------------------------------------------------------------ news

def ingest_news(db: Session, items: list[dict], dedupe_window_days: int = 3) -> dict:
    """Insert news items, dedup by URL (case-insensitive). Returns counts.

    Items that match an existing URL are skipped and counted as duplicates.
    """
    by_url: dict[str, dict] = {}
    for item in items:
        url = (item.get("url") or "").strip()
        if not url:
            continue
        by_url.setdefault(url.lower(), item)

    existing_urls = set(
        db.execute(
            select(NewsArticle.url).where(
                NewsArticle.url.in_([u.lower() for u in by_url])
            )
        ).scalars()
    )
    # Also normalize stored URLs lowercase for consistent dedupe.
    existing_urls |= {
        u.lower()
        for u in db.execute(
            select(NewsArticle.url).where(
                NewsArticle.url.in_([u for u in by_url])
            )
        ).scalars()
    }

    inserted = 0
    duplicates = 0
    new_articles: list[NewsArticle] = []
    for url, item in by_url.items():
        if url in existing_urls:
            duplicates += 1
            continue
        published = item.get("published_at")
        if published is not None and published.tzinfo is None:
            published = published.replace(tzinfo=UTC)
        article = NewsArticle(
            source=item.get("source") or "rss",
            url=url,
            title=item.get("title") or "",
            summary=item.get("summary"),
            author=item.get("author"),
            published_at=published,
            missing_timestamp=bool(item.get("missing_timestamp")),
            stale_delivery=bool(item.get("stale_delivery")),
            assets=json.dumps(item.get("assets") or []),
        )
        db.add(article)
        new_articles.append(article)
        inserted += 1

    db.flush()  # assign ids for NewsAsset FKs
    for article in new_articles:
        for canonical_symbol in json.loads(article.assets or "[]"):
            db.add(NewsAsset(news_id=article.id, symbol=canonical_symbol))
    db.commit()
    return {"inserted": inserted, "duplicates": duplicates, "total": len(by_url)}


# ------------------------------------------------------------------ provider health

def record_provider_success(db: Session, provider: str, message: str | None = None) -> None:
    row = db.execute(
        select(ProviderHealth).where(ProviderHealth.provider == provider)
    ).scalar_one_or_none()
    if row is None:
        db.add(
            ProviderHealth(
                provider=provider,
                status="ok",
                last_success_at=_now(),
                error_count=0,
                message=message,
            )
        )
    else:
        row.status = "ok"
        row.last_success_at = _now()
        row.error_count = 0
        row.message = message
    db.commit()


def record_provider_error(db: Session, provider: str, error: Exception, message: str | None = None) -> None:
    row = db.execute(
        select(ProviderHealth).where(ProviderHealth.provider == provider)
    ).scalar_one_or_none()
    if row is None:
        db.add(
            ProviderHealth(
                provider=provider,
                status="down",
                last_error=str(error)[:4000],
                error_count=1,
                message=message,
            )
        )
    else:
        row.status = "down"
        row.last_error = str(error)[:4000]
        row.error_count = (row.error_count or 0) + 1
        row.message = message
    db.commit()
