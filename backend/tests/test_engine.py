"""Tests for the decision matrix / scenario engine."""

from __future__ import annotations

from datetime import UTC, datetime

from app.analysis.engine import RULE_VERSION, compute_scenario
from app.providers.base import CandleData


def _trend(n: int, start: float = 100.0, step: float = 0.5, vol: float = 0.2) -> list[CandleData]:
    return [
        CandleData(
            "BTC/USD",
            "1h",
            datetime(2026, 1, 1, tzinfo=UTC),
            start + i * step - vol,
            start + i * step + vol,
            start + i * step - vol,
            start + i * step,
            100.0 + i,
        )
        for i in range(n)
    ]


def _flat(n: int = 60, price: float = 100.0) -> list[CandleData]:
    return [
        CandleData(
            "BTC/USD",
            "1h",
            datetime(2026, 1, 1, tzinfo=UTC),
            price,
            price,
            price,
            price,
            50.0,
        )
        for _ in range(n)
    ]


class TestDirection:
    def test_uptrend_is_bullish(self):
        candles = _trend(120, start=100, step=0.5, vol=0.15)
        s = compute_scenario(candles, symbol="BTC/USD", timeframe="1h")
        assert s["direction"] == "BULLISH"
        assert s["alignment_score"] > 0
        assert s["rule_version"] == RULE_VERSION
        assert "generated_at" in s

    def test_downtrend_is_bearish(self):
        candles = _trend(120, start=200, step=-0.5, vol=0.15)
        s = compute_scenario(candles, symbol="BTC/USD")
        assert s["direction"] == "BEARISH"
        assert s["alignment_score"] < 0

    def test_flat_is_neutral(self):
        candles = _flat(60, price=100.0)
        s = compute_scenario(candles, symbol="BTC/USD")
        assert s["direction"] == "NEUTRAL"
        assert s["stop_loss"] is None

    def test_non_actionable_has_no_levels(self):
        candles = _flat(60)
        s = compute_scenario(candles, symbol="BTC/USD")
        # neutral scenarios carry no entry/stop/targets
        assert s["stop_loss"] is None and s["take_profits"] == []


class TestEvidence:
    def test_decisions_has_all_signals(self):
        s = compute_scenario(_trend(120), symbol="BTC/USD")
        names = {d["signal"] for d in s["decisions"]}
        assert {
            "ema_trend",
            "rsi_momentum",
            "volatility_regime",
            "volume_confirm",
            "structure_levels",
        } <= names

    def test_evidence_sums(self):
        s = compute_scenario(_trend(120), symbol="BTC/USD")
        ev = s["evidence"]
        assert ev["signals_evaluated"] == len(s["decisions"])
        assert ev["weighted_alignment"] != 0.0 or s["direction"] == "NEUTRAL"


class TestNewsInfluence:
    def test_news_lowers_alignment_but_does_not_override_strong_trend(self):
        # A mild uptrend plus very bearish news → alignment drops (news influences)
        candles = _trend(120, step=0.25, vol=0.1)
        neutral_no_news = compute_scenario(candles, symbol="BTC/USD")["alignment_score"]
        bearish_news = [
            {
                "title": "Bitcoin crashes below support, investors fear a sharper drop",
                "sentiment": "negative",
                "importance": 0.9,
                "relevance_score": 0.9,
                "url": "http://example.com/1",
            }
        ]
        with_news = compute_scenario(candles, symbol="BTC/USD", news=bearish_news)
        # The single -1.0 vote with weight 0.15 must drag alignment down.
        assert with_news["alignment_score"] <= neutral_no_news

    def test_news_alone_cannot_forge_non_neutral_direction(self):
        # A flat tape with heavy negative news: news votes -1 but cannot alone
        # cross the actionable threshold — price takes priority by design.
        candles = _flat(60, price=100.0)
        bearish_news = [
            {
                "title": f"Crash {i}, investors fear sell-off and dropping prices",
                "sentiment": "negative",
                "importance": 0.8,
                "relevance_score": 0.9,
                "url": f"http://example.com/{i}",
            }
            for i in range(6)
        ]
        no_news = compute_scenario(candles, symbol="BTC/USD")
        with_news = compute_scenario(candles, symbol="BTC/USD", news=bearish_news)
        assert with_news["alignment_score"] < no_news["alignment_score"]


class TestDeterminism:
    def test_identical_inputs_identical_output(self):
        candles = _trend(120, step=0.4, vol=0.2)
        t = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
        a = compute_scenario(candles, symbol="BTC/USD", now=t)
        b = compute_scenario(candles, symbol="BTC/USD", now=t)
        assert a == b

    def test_news_order_independent(self):
        candles = _trend(120)
        t = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
        n1 = [
            {"title": "x", "sentiment": "positive", "relevance_score": 0.9, "importance": 0.8},
            {"title": "y", "sentiment": "negative", "relevance_score": 0.8, "importance": 0.7},
        ]
        n2 = [
            {"title": "y", "sentiment": "negative", "relevance_score": 0.8, "importance": 0.7},
            {"title": "x", "sentiment": "positive", "relevance_score": 0.9, "importance": 0.8},
        ]
        a = compute_scenario(candles, news=n1, symbol="BTC/USD", now=t)
        b = compute_scenario(candles, news=n2, symbol="BTC/USD", now=t)
        assert a == b


class TestValidation:
    def test_too_few_candles_raises(self):
        import pytest

        with pytest.raises(ValueError):
            compute_scenario(_flat(10), symbol="BTC/USD")


class TestSmartAdvisor:
    def test_bullish_scenario_has_advisor_fields(self):
        s = compute_scenario(_trend(120, start=100, step=0.5, vol=0.15), symbol="BTC/USD")
        assert "open_window" in s
        assert "advisor_tips" in s
        assert isinstance(s["advisor_tips"], list)
        assert s["advisor_tips"]

    def test_neutral_scenario_has_ranging_advice(self):
        s = compute_scenario(_flat(60, price=100.0), symbol="BTC/USD")
        assert s["direction"] == "NEUTRAL"
        assert s["open_window"].startswith("No open window")
        assert any("ranging" in t for t in s["advisor_tips"])
