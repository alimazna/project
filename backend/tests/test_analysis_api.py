"""Tests for the analysis API: scenario run/persist/read + backtest."""

from datetime import UTC, datetime, timedelta

from app.models import NewsArticle
from app.providers.base import CandleData
from app.services.ingestion import ensure_symbols, ingest_news, upsert_candles


def _seed(db, n_candles: int = 60, step: float = 0.3, symbol: str = "BTC/USD"):
    ensure_symbols(
        db,
        [
            {
                "symbol": symbol,
                "base": symbol.split("/")[0],
                "quote": symbol.split("/")[1],
                "display_name": "Test",
            }
        ],
    )
    t0 = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    upsert_candles(
        db,
        [
            CandleData(
                symbol,
                "1h",
                t0 + timedelta(hours=i),
                open=100 + i * step,
                high=100 + i * step + 0.2,
                low=100 + i * step - 0.2,
                close=100 + i * step,
                volume=100.0 + i,
            )
            for i in range(n_candles)
        ],
    )
    ingest_news(
        db,
        [
            {
                "source": "TestFeed",
                "url": f"https://feed.test/{symbol.replace('/', '-')}",
                "title": "Bitcoin momentum strengthens",
                "published_at": t0,
                "assets": [symbol],
            }
        ],
    )
    # The ingestion layer stores raw rows; production scoring is applied by the
    # news pipeline. Here we emulate a scored article for the engine to consume.
    article = db.query(NewsArticle).first()
    article.sentiment = "positive"
    article.relevance_score = 0.9
    article.importance = 0.7
    db.commit()


class TestAnalysisRun:
    def test_run_persists_and_returns_scenario(self, client, db_session):
        _seed(db_session)
        resp = client.post("/api/v1/analysis/run?symbol=BTC%2FUSD&interval=1h&limit=60")
        assert resp.status_code == 200
        body = resp.json()
        assert body["saved_scenario_id"] is not None
        s = body["scenario"]
        assert s["symbol"] == "BTC/USD"
        assert s["direction"] in ("BULLISH", "BEARISH", "NEUTRAL")
        assert "rule_version" in s and s["rule_version"].startswith("matrix.")
        assert "decisions" in s and "evidence" in s

    def test_run_rejects_missing_data(self, client, db_session):
        resp = client.post("/api/v1/analysis/run?symbol=ETH%2FUSD&interval=1h&limit=60")
        assert resp.status_code == 404


class TestScenarioReadback:
    def test_list_and_get_scenario(self, client, db_session):
        _seed(db_session)
        client.post("/api/v1/analysis/run?symbol=BTC%2FUSD&interval=1h&limit=60")
        listing = client.get("/api/v1/analysis/scenarios")
        assert listing.status_code == 200
        rows = listing.json()["scenarios"]
        assert len(rows) >= 1
        first_id = rows[0]["id"]
        full = client.get(f"/api/v1/analysis/scenarios/{first_id}")
        assert full.status_code == 200
        assert full.json()["scenario"]["decisions"]


class TestBacktestEndpoint:
    def test_backtest_returns_stats(self, client, db_session):
        _seed(db_session, n_candles=120, step=0.3)
        resp = client.get(
            "/api/v1/analysis/backtest?symbol=BTC%2FUSD&interval=1h&limit=120&hold_bars=5"
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "stats" in body and body["stats"]["trades"] > 0
        assert "results" in body and body["config"]["hold_bars"] == 5

