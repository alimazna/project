"""Tests for the data-ingestion persistence layer and providers."""

from datetime import UTC, datetime, timedelta

from app.providers.base import CandleData, TickerData
from app.providers.market.kraken import _interval_minutes, _kraken_pair
from app.providers.market.okx import _inst_id
from app.providers.news.rss import _parse_published, _strip_utm
from app.services.ingestion import (
    ensure_symbols,
    ingest_news,
    latest_candle_time,
    upsert_candles,
    upsert_ticker,
)


class TestSymbolPairMapping:
    def test_kraken_pair(self):
        assert _kraken_pair("BTC/USD") == "XBTUSD"
        assert _kraken_pair("ETH/USD") == "ETHUSD"
        assert _kraken_pair("XRP/USD") == "XRPUSD"

    def test_interval_minutes(self):
        assert _interval_minutes("1h") == 60
        assert _interval_minutes("1d") == 1440
        assert _interval_minutes("30m") == 30

    def test_okx_inst_id_usd_to_usdt(self):
        assert _inst_id("BTC/USD") == "BTC-USDT"
        assert _inst_id("OP/USDT") == "OP-USDT"


class TestRSSCleanup:
    def test_strip_utm(self):
        url = "https://example.com/news?a=1&utm_source=rss_feed&b=2"
        assert _strip_utm(url) == "https://example.com/news?a=1&b=2"
        assert "utm_" not in _strip_utm(url)

    def test_parse_published_with_tuple(self):
        # feedparser-style published_parsed tuple
        entry = {"published_parsed": (2026, 10, 17, 10, 30, 0, 5, 290, 0)}
        dt, missing = _parse_published(entry)
        assert missing is False
        assert dt is not None and dt.year == 2026

    def test_parse_published_missing(self):
        dt, missing = _parse_published({})
        assert missing is True
        assert dt is None


class TestIngestionPersistence:
    def test_ensure_symbols_upserts(self, db_session):
        ensure_symbols(
            db_session,
            [
                {"symbol": "BTC/USD", "base": "BTC", "quote": "USD", "display_name": "Bitcoin"}
            ],
        )
        from app.models import Symbol

        assert db_session.get(Symbol, "BTC/USD") is not None

    def test_upsert_candles_and_latest(self, db_session):
        t0 = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
        candles = [
            CandleData("BTC/USD", "1h", t0, 100.0, 110.0, 90.0, 105.0, 10.0),
            CandleData("BTC/USD", "1h", t0 + timedelta(hours=1), 105.0, 115.0, 100.0, 110.0, 12.0),
        ]
        inserted = upsert_candles(db_session, candles)
        assert inserted == 2
        latest = latest_candle_time(db_session, "BTC/USD", "1h")
        assert latest is not None and latest == t0 + timedelta(hours=2)  # close_time of 2nd candle

        # upserting same candle returns 0 new rows
        again = upsert_candles(db_session, [candles[0]])
        assert again == 0

    def test_upsert_ticker_persists(self, db_session):
        ticker = TickerData("BTC/USD", 50000.0, high_24h=51000.0, low_24h=49000.0)
        upsert_ticker(db_session, ticker)
        from app.models import Ticker

        row = db_session.query(Ticker).filter_by(symbol="BTC/USD").first()
        assert row is not None
        assert row.last_price == 50000.0

    def test_ingest_news_dedupe(self, db_session):
        items = [
            {
                "source": "CoinTelegraph",
                "url": "https://cointelegraph.com/news/a",
                "title": "First",
                "published_at": datetime(2026, 10, 17, 8, 0, tzinfo=UTC),
            },
            {
                "source": "CoinDesk",
                "url": "https://coindesk.com/news/b",
                "title": "Second",
                "published_at": None,
            },
        ]
        result = ingest_news(db_session, items)
        assert result["inserted"] == 2

        # same URL again -> duplicate
        result2 = ingest_news(db_session, [items[0]])
        assert result2["inserted"] == 0
        assert result2["duplicates"] >= 1

    def test_ingest_news_assets(self, db_session):
        items = [
            {
                "source": "CoinTelegraph",
                "url": "https://cointelegraph.com/news/x",
                "title": "Bitcoin gains",
                "assets": ["BTC/USD"],
            }
        ]
        ingest_news(db_session, items)
        from app.models import NewsArticle, NewsAsset

        article = db_session.query(NewsArticle).first()
        assert article is not None
        asset = db_session.query(NewsAsset).filter_by(news_id=article.id).first()
        assert asset is not None
        assert asset.symbol == "BTC/USD"
