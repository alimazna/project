"""High-level ingestion runners used by background workers and CLI."""

from __future__ import annotations

import logging
from datetime import timedelta

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.symbols import default_symbols
from app.providers.market.kraken import KrakenProvider
from app.providers.market.okx import OKXProvider
from app.providers.news.registry import get_news_provider
from app.services.ingestion import (
    ensure_symbols,
    ingest_news,
    latest_candle_time,
    record_provider_error,
    record_provider_success,
    upsert_candles,
    upsert_ticker,
)

logger = logging.getLogger(__name__)


def run_candle_sync(db: Session, symbols=None, interval: str | None = None) -> dict:
    """Pull candles + tickers for the configured symbol set.

    Uses Kraken as primary; OKX as secondary/fallback for missing pairs.
    History backfill is incremental (from last stored candle close).
    """
    interval = interval or settings.candle_inteval_default
    symbols = symbols or [
        {"symbol": s.symbol, "base": s.base, "quote": s.quote, "display_name": s.display_name}
        for s in default_symbols()
    ]
    ensure_symbols(db, symbols)

    kraken = KrakenProvider()
    okx = OKXProvider()
    summary = {"symbols": len(symbols), "candles_inserted": 0, "tickers": 0, "errors": []}

    try:
        for sym in symbols:
            symbol = sym["symbol"]
            try:
                since = latest_candle_time(db, symbol, interval)
                candles = kraken.fetch_klines(
                    symbol, interval, limit=200, since=since - timedelta(minutes=5) if since else None
                )
                summary["candles_inserted"] += upsert_candles(db, candles)

                ticker = kraken.fetch_ticker(symbol)
                if ticker is not None:
                    upsert_ticker(db, ticker)
                    summary["tickers"] += 1
                else:
                    # fallback to OKX
                    ticker = okx.fetch_ticker(symbol)
                    if ticker is not None:
                        upsert_ticker(db, ticker)
                        summary["tickers"] += 1
            except Exception as exc:  # per-symbol failure does not kill the run
                logger.warning("%s sync failed: %s", symbol, exc)
                summary["errors"].append({"symbol": symbol, "error": str(exc)})
        record_provider_success(db, "kraken")
    except Exception as exc:
        record_provider_error(db, "kraken", exc)
        summary["errors"].append({"fatal": str(exc)})
    finally:
        kraken.close()
        okx.close()

    return summary


def run_ticker_sync(db: Session, symbols=None) -> dict:
    """Refresh latest tickers for all tracked symbols (cheap, frequent)."""
    symbols = symbols or [
        {"symbol": s.symbol, "base": s.base, "quote": s.quote, "display_name": s.display_name}
        for s in default_symbols()
    ]
    ensure_symbols(db, symbols)
    kraken = KrakenProvider()
    okx = OKXProvider()
    summary = {"tickers": 0, "errors": []}
    for sym in symbols:
        symbol = sym["symbol"]
        try:
            ticker = kraken.fetch_ticker(symbol) or okx.fetch_ticker(symbol)
            if ticker is not None:
                upsert_ticker(db, ticker)
                summary["tickers"] += 1
        except Exception as exc:
            summary["errors"].append({"symbol": symbol, "error": str(exc)})
    record_provider_success(db, "kraken")
    kraken.close()
    okx.close()
    return summary


def run_news_sync(db: Session) -> dict:
    """Fetch + persist news from configured RSS feeds."""
    provider = get_news_provider()
    try:
        items = provider.fetch()
        result = ingest_news(db, items)
        record_provider_success(db, f"news.{provider.name}", f"{result['inserted']} new articles")
        return result
    except Exception as exc:
        record_provider_error(db, f"news.{provider.name}", exc)
        return {"inserted": 0, "duplicates": 0, "total": 0, "error": str(exc)}
