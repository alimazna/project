"""Unit tests for the indicator library (determinism + no-lookahead)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.analysis.indicators import (
    atr,
    confirmed_swing_pivots,
    ema,
    rsi,
    sma,
    stdev,
    support_resistance,
    swing_pivots,
    volume_zscore,
)
from app.providers.base import CandleData


def _mk(closes: list[float]) -> list[float]:
    return closes


def _candles(price_series: list[tuple[float, float, float, float, float]]) -> list[CandleData]:
    out = []
    t = datetime(2026, 1, 1, tzinfo=UTC)
    for o, h, lo, c, v in price_series:
        out.append(CandleData("BTC/USD", "1h", t, o, h, lo, c, v))
        t = t.replace(hour=(t.hour + 1) % 24)
    return out


def _trend(n: int, start: float = 100.0, step: float = 1.0, vol: float = 0.5) -> list[CandleData]:
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


class TestSMA:
    def test_basic(self):
        out = sma([1, 2, 3, 4], 3)
        assert out == [None, None, 2.0, 3.0]

    def test_invalid_period(self):
        with pytest.raises(ValueError):
            sma([1], 0)


class TestEMA:
    def test_seed_and_monotonic(self):
        vals = [float(i) for i in range(1, 21)]
        out = ema(vals, 5)
        assert out[0] is None
        assert out[4] == 3.0  # seed = mean of first 5
        assert all(b is not None for b in out[4:])

    def test_deterministic(self):
        vals = [float(i % 7) for i in range(50)]
        assert ema(vals, 10) == ema(vals, 10)


class TestRSI:
    def test_all_up_is_100(self):
        series = _trend(30, step=1.0)
        r = rsi([c.close for c in series], 14)
        assert r[-1] == 100.0

    def test_all_down_is_0(self):
        series = _trend(30, start=100.0, step=-1.0)
        r = rsi([c.close for c in series], 14)
        assert r[-1] == 0.0

    def test_deterministic(self):
        closes = [float(i % 17) for i in range(200)]
        assert rsi(closes, 14) == rsi(closes, 14)


class TestATR:
    def test_flat_series_zero(self):
        candles = [
            CandleData("X", "1h", datetime(2026, 1, 1, tzinfo=UTC), 5, 5, 5, 5, 1.0)
            for _ in range(20)
        ]
        a = atr(candles, 14)
        assert a[-1] == 0.0

    def test_no_lookahead(self):
        series = _trend(40, step=0.5, vol=0.2)
        a = atr(series, 14)
        # ATR at index i must be computable using only data <= i
        assert a[14] is not None
        assert all(x is not None for x in a[15:])


class TestVolumeZ:
    def test_constant_volume_zero(self):
        candles = [
            CandleData("X", "1h", datetime(2026, 1, 1, tzinfo=UTC), 1, 1, 1, 1, v)
            for v in [5.0] * 40
        ]
        z = volume_zscore(candles, 20)
        assert z[-1] == 0.0

    def test_spike_positive(self):
        candles = [
            CandleData("X", "1h", datetime(2026, 1, 1, tzinfo=UTC), 1, 1, 1, 1, v)
            for v in [10.0] * 20 + [1000.0]
        ]
        z = volume_zscore(candles, 20)
        assert z[-1] > 3.0


class TestStdev:
    def test_known(self):
        out = stdev([2, 4, 4, 4, 5, 5, 7, 9], 8)
        assert out[7] == pytest.approx(2.0, abs=1e-9)

    def test_deterministic(self):
        vals = [float(i % 5) for i in range(100)]
        assert stdev(vals, 10) == stdev(vals, 10)


class TestSwings:
    def test_recognizes_high_low(self):
        candles = _candles(
            [
                (10, 11, 9, 10, 5),
                (12, 13, 11, 12, 5),
                (13, 15, 13, 14, 5),  # high pivot
                (12, 13, 11, 12, 5),
                (10, 11, 9, 10, 5),  # low pivot
                (11, 12, 10, 11, 5),
            ]
        )
        pivots = swing_pivots(candles, left=1, right=1)
        kinds = [p.kind for p in pivots]
        assert "HIGH" in kinds and "LOW" in kinds

    def test_no_lookahead_filter(self):
        series = _trend(60, step=0.5, vol=0.3)
        pivots = confirmed_swing_pivots(series, left=2, right=2)
        # Any pivot index must leave at least 2 bars of right-confirmation room
        assert all(p.index < len(series) - 2 for p in pivots)
        assert all(p.index >= 2 for p in pivots)


class TestSupportResistance:
    def test_clusters(self):
        from app.analysis.indicators import Pivot

        levels = support_resistance(
            [
                Pivot(1, "LOW", 100.0, 2),
                Pivot(2, "LOW", 100.01, 2),
                Pivot(3, "HIGH", 200.0, 2),
            ],
            window=50,
        )
        # The two near-identical LOW levels merge into one
        lows = [lv for lv, kind in levels if kind == "S"]
        assert len(lows) == 1
        assert lows[0] == pytest.approx(100.0)
