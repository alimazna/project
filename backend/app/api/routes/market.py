"""Market data read endpoints: candles, tickers, symbols, news."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Candle, NewsArticle, NewsAsset, Symbol, Ticker

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/symbols")
def list_symbols(
    db: Session = Depends(get_db),
    quote: str | None = Query(None, description="Filter by quote (USD, USDT...)"),
    active: bool = True,
) -> dict:
    q = select(Symbol)
    if quote:
        q = q.where(Symbol.quote == quote)
    if active is not None:
        q = q.where(Symbol.is_active == active)
    symbols = db.execute(q.order_by(Symbol.symbol)).scalars().all()
    return {
        "symbols": [
            {
                "symbol": s.symbol,
                "base": s.base,
                "quote": s.quote,
                "display_name": s.display_name,
                "provider": s.provider,
            }
            for s in symbols
        ]
    }


@router.get("/candles/{symbol:path}")
def get_candles(
    symbol: str,
    db: Session = Depends(get_db),
    interval: str = Query("1h", description="1m|5m|15m|30m|1h|4h|1d|1w"),
    limit: int = Query(200, ge=1, le=1000),
) -> dict:
    rows = (
        db.execute(
            select(Candle)
            .where(Candle.symbol == symbol.upper(), Candle.interval == interval)
            .order_by(Candle.open_time.desc())
            .limit(limit)
        )
        .scalars()
        .all()
    )
    if not rows:
        raise HTTPException(404, "No candles found for symbol/interval")
    return {
        "symbol": symbol.upper(),
        "interval": interval,
        "candles": [candle_to_dict(c) for c in reversed(rows)],
    }


def candle_to_dict(c: Candle) -> dict:
    return {
        "open_time": _iso(c.open_time),
        "close_time": _iso(c.close_time),
        "open": c.open,
        "high": c.high,
        "low": c.low,
        "close": c.close,
        "volume": c.volume,
        "closed": c.closed,
    }


def _iso(dt: datetime) -> str:
    if dt is None:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.isoformat()


@router.get("/tickers")
def list_tickers(
    db: Session = Depends(get_db),
    symbol: str | None = Query(None),
) -> dict:
    """Latest ticker per symbol (most recent fetch)."""
    # Window function ranks rows per symbol by fetch recency; keeps only rn=1.
    ranked = (
        select(
            Ticker.id,
            func.row_number()
            .over(partition_by=Ticker.symbol, order_by=Ticker.fetched_at.desc())
            .label("rn"),
        ).subquery()
    )
    q = (
        select(Ticker)
        .join(ranked, Ticker.id == ranked.c.id)
        .where(ranked.c.rn == 1)
        .order_by(Ticker.symbol)
    )
    if symbol:
        q = q.where(Ticker.symbol == symbol.upper())
    rows = db.execute(q).scalars().all()
    return {
        "tickers": [
            {
                "symbol": t.symbol,
                "last_price": t.last_price,
                "high_24h": t.high_24h,
                "low_24h": t.low_24h,
                "volume_24h": t.volume_24h,
                "change_24h_pct": t.change_24h_pct,
                "fetched_at": _iso(t.fetched_at),
            }
            for t in rows
        ]
    }


@router.get("/news")
def list_news(
    db: Session = Depends(get_db),
    limit: int = Query(30, ge=1, le=100),
    source: str | None = Query(None),
    symbol: str | None = Query(None),
    since: str | None = Query(None, description="ISO datetime; only articles published after"),
) -> dict:
    q = select(NewsArticle).order_by(NewsArticle.published_at.desc().nullslast())
    if symbol and symbol.upper():
        # Filter via the normalized assets join (symbols match, e.g. "BTC/USD").
        q = q.join(NewsAsset, NewsArticle.id == NewsAsset.news_id).where(
            NewsAsset.symbol == symbol.upper()
        )
    if source:
        q = q.where(NewsArticle.source == source)
    if since:
        try:
            since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(422, "Invalid 'since' ISO datetime") from None
        q = q.where(NewsArticle.published_at >= since_dt)
    rows = db.execute(q).scalars().all()
    return {
        "articles": [
            {
                "id": a.id,
                "source": a.source,
                "url": a.url,
                "title": a.title,
                "summary": a.summary,
                "author": a.author,
                "published_at": _iso(a.published_at),
                "sentiment": a.sentiment,
                "relevance_score": a.relevance_score,
                "assets": a.assets,
            }
            for a in rows
        ]
    }
