"""Tests for the market-data read API (symbols, candles, tickers, news)."""

from datetime import UTC, datetime, timedelta

from app.providers.base import CandleData, TickerData
from app.services.ingestion import ensure_symbols, ingest_news, upsert_candles, upsert_ticker


def _seed_market(db):
    ensure_symbols(
        db,
        [{"symbol": "BTC/USD", "base": "BTC", "quote": "USD", "display_name": "Bitcoin"}],
    )
    t0 = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    upsert_candles(
        db,
        [
            CandleData("BTC/USD", "1h", t0, 100.0, 110.0, 90.0, 105.0, 10.0),
            CandleData("BTC/USD", "1h", t0 + timedelta(hours=1), 105.0, 115.0, 100.0, 110.0, 12.0),
        ],
    )
    upsert_ticker(db, TickerData("BTC/USD", 105.0, high_24h=115.0, low_24h=90.0))
    ingest_news(
        db,
        [
            {
                "source": "CoinTelegraph",
                "url": "https://cointelegraph.com/news/btc",
                "title": "Bitcoin rally",
                "published_at": t0,
                "assets": ["BTC/USD"],
            }
        ],
    )


class TestMarketEndpoints:
    def test_symbols(self, client, db_session):
        _seed_market(db_session)
        resp = client.get("/api/v1/market/symbols")
        assert resp.status_code == 200
        symbols = resp.json()["symbols"]
        assert any(s["symbol"] == "BTC/USD" for s in symbols)

    def test_candles(self, client, db_session):
        _seed_market(db_session)
        resp = client.get("/api/v1/market/candles/BTC/USD?interval=1h&limit=2")
        assert resp.status_code == 200
        body = resp.json()
        assert body["symbol"] == "BTC/USD"
        assert len(body["candles"]) == 2
        assert body["candles"][-1]["close"] == 110.0

    def test_candles_unknown_symbol_404(self, client, db_session):
        _seed_market(db_session)
        resp = client.get("/api/v1/market/candles/NOPE/USD?interval=1h")
        assert resp.status_code == 404

    def test_tickers(self, client, db_session):
        _seed_market(db_session)
        resp = client.get("/api/v1/market/tickers")
        assert resp.status_code == 200
        tickers = resp.json()["tickers"]
        assert any(t["symbol"] == "BTC/USD" and t["last_price"] == 105.0 for t in tickers)

    def test_news(self, client, db_session):
        _seed_market(db_session)
        resp = client.get("/api/v1/market/news")
        assert resp.status_code == 200
        assert resp.json()["articles"][0]["title"] == "Bitcoin rally"

    def test_news_filter_symbol(self, client, db_session):
        _seed_market(db_session)
        resp = client.get("/api/v1/market/news?symbol=BTC/USD")
        assert resp.status_code == 200
        assert len(resp.json()["articles"]) >= 1
