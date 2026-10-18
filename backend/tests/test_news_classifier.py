"""Unit tests for the deterministic news classifier."""

from __future__ import annotations

from datetime import UTC, datetime

from app.analysis.news_classifier import _match_assets, classify_news


class TestSentiment:
    def test_positive_detected(self):
        result = classify_news("Bitcoin surges to record high as ETF inflows rocket")
        assert result["sentiment"] == "positive"

    def test_negative_detected(self):
        result = classify_news("Ethereum crashes below support, investors fear sell-off")
        assert result["sentiment"] == "negative"

    def test_neutral(self):
        result = classify_news("Kraken lists new stablecoin pair")
        assert result["sentiment"] == "neutral"

    def test_mixed_score(self):
        result = classify_news("Bitcoin rallies but traders fear a sharp drop later")
        assert result["sentiment"] in ("mixed", "positive", "negative")


class TestAssetMapping:
    def test_bitcoin_aliases(self):
        counts = _match_assets("Bitcoin and BTC hit new highs")
        assert counts["BTC/USD"] >= 2

    def test_solana_not_sol_text(self):
        counts = _match_assets("Solar energy is rising, but SOL tokens also rally")
        # "solar" starts with "sol" but isn't the token "sol"
        assert counts.get("SOL/USD", 0) == 1

    def test_ethereum_classic_phrase(self):
        counts = _match_assets("Ethereum Classic network upgrade")
        assert counts.get("ETC/USD", 0) >= 1


class TestRelevance:
    def test_multiple_mentions_high_relevance(self):
        result = classify_news("Bitcoin, Bitcoin and more Bitcoin news today")
        assert result["relevance_score"] > 0.5

    def test_no_asset_low_relevance(self):
        result = classify_news("Global markets mixed after election results")
        assert result["relevance_score"] < 0.5


class TestDeterminism:
    def test_same_input_same_output(self):
        a = classify_news("Bitcoin rallies on ETF inflows", "Strong volume confirms the move")
        b = classify_news("Bitcoin rallies on ETF inflows", "Strong volume confirms the move")
        assert a == b

    def test_identifier_version(self):
        assert classify_news("x")["classifier_version"] == "lexicon.v0.1.0"


class TestRecency:
    def test_fresh_news_boosted(self):
        now = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
        fresh = datetime(2026, 1, 1, 11, 0, tzinfo=UTC)
        old = datetime(2025, 12, 1, 11, 0, tzinfo=UTC)
        r_fresh = classify_news("Bitcoin rallies", published_at=fresh, now=now)
        r_old = classify_news("Bitcoin rallies", published_at=old, now=now)
        assert r_fresh["importance"] > r_old["importance"]
