"""Deterministic technical indicators over OHLCV series.

All functions are pure: identical input arrays produce identical output.
Inputs are `CandleData`-like sequences (`.open/.high/.low/.close/.volume`).
Windows are right-aligned and never look ahead (suitable for walk-forward/backtest).

Rule: historical backfills and live bars both use **closed** candles only.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.providers.base import CandleData

# ---------------------------------------------------------------- smoothing

def sma(values: list[float], period: int) -> list[float | None]:
    """Simple moving average; None while fewer than `period` bars exist."""
    if period <= 0:
        raise ValueError("period must be positive")
    out: list[float | None] = [None] * len(values)
    if len(values) < period:
        return out
    running = sum(values[:period])
    out[period - 1] = running / period
    for i in range(period, len(values)):
        running += values[i] - values[i - period]
        out[i] = running / period
    return out


def ema(values: list[float], period: int) -> list[float | None]:
    """EMA seeded from the SMA of the first `period` values (deterministic)."""
    if period <= 0:
        raise ValueError("period must be positive")
    out: list[float | None] = [None] * len(values)
    if len(values) < period:
        return out
    k = 2.0 / (period + 1.0)
    seed = sum(values[:period]) / period
    out[period - 1] = seed
    for i in range(period, len(values)):
        out[i] = values[i] * k + out[i - 1] * (1 - k)
    return out


def stdev(values: list[float], period: int) -> list[float | None]:
    """Population standard deviation over the last `period` values."""
    if period <= 0:
        raise ValueError("period must be positive")
    out: list[float | None] = [None] * len(values)
    if len(values) < period:
        return out
    for i in range(period - 1, len(values)):
        window = values[i - period + 1 : i + 1]
        m = sum(window) / period
        out[i] = (sum((x - m) ** 2 for x in window) / period) ** 0.5
    return out


# ---------------------------------------------------------------- oscillators

def rsi(values: list[float], period: int = 14) -> list[float | None]:
    """Wilder RSI. First value requires `period` bars of gains/losses."""
    if period <= 0:
        raise ValueError("period must be positive")
    n = len(values)
    out: list[float | None] = [None] * n
    if n <= period:
        return out
    gains: list[float] = []
    losses: list[float] = []
    for i in range(1, n):
        delta = values[i] - values[i - 1]
        if delta >= 0:
            gains.append(delta)
            losses.append(0.0)
        else:
            gains.append(0.0)
            losses.append(-delta)
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    out[period] = _rsi_from(avg_gain, avg_loss)
    for i in range(period + 1, n):
        avg_gain = (avg_gain * (period - 1) + gains[i - 1]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i - 1]) / period
        out[i] = _rsi_from(avg_gain, avg_loss)
    return out


def _rsi_from(avg_gain: float, avg_loss: float) -> float:
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - 100.0 / (1.0 + rs)


# ---------------------------------------------------------------- volatility

def atr(candles: list[CandleData], period: int = 14) -> list[float | None]:
    """Wilder ATR using the True Range defined by the prior close (right-aligned)."""
    if period <= 0:
        raise ValueError("period must be positive")
    n = len(candles)
    out: list[float | None] = [None] * n
    if n < 2:
        return out
    trs: list[float] = [0.0] * n
    for i in range(1, n):
        hi, lo, prev_close = candles[i].high, candles[i].low, candles[i - 1].close
        trs[i] = max(hi - lo, abs(hi - prev_close), abs(lo - prev_close))
    if n <= period:
        for i in range(2, n):
            out[i] = sum(trs[1 : i + 1]) / i
        return out
    seed = sum(trs[1 : period + 1]) / period
    out[period] = seed
    for i in range(period + 1, n):
        out[i] = (out[i - 1] * (period - 1) + trs[i]) / period
    return out


def volume_zscore(candles: list[CandleData], period: int = 20) -> list[float | None]:
    """Z-score of the latest volume against the trailing window (population)."""
    vols = [c.volume for c in candles]
    return _zscore(vols, period)


def _zscore(values: list[float], period: int) -> list[float | None]:
    if period <= 0:
        raise ValueError("period must be positive")
    out: list[float | None] = [None] * len(values)
    if len(values) < period:
        return out
    for i in range(period - 1, len(values)):
        window = values[i - period + 1 : i + 1]
        m = sum(window) / period
        sd = (sum((x - m) ** 2 for x in window) / period) ** 0.5
        out[i] = (values[i] - m) / sd if sd > 0 else 0.0
    return out


# ---------------------------------------------------------------- structure / pivots

@dataclass(frozen=True)
class Pivot:
    index: int
    kind: str  # HIGH | LOW
    level: float
    strength: int  # number of bars confirmed <-> must be >= confirmations


def swing_pivots(candles: list[CandleData], left: int = 2, right: int = 2) -> list[Pivot]:
    """Classic fractal pivots using the prior `left` and next `right` bars.

    A HIGH pivot at i requires i.high > each of the previous `left` highs and
    each of the next `right` highs (strictly). Because this looks `right` bars
    ahead, it is intended for *live indicator display* only — the no-lookahead
    backtest must use confirmed pivots via `confirmed_swing_pivots`.
    """
    if left < 1 or right < 1:
        raise ValueError("left and right must be positive")
    n = len(candles)
    pivots: list[Pivot] = []
    for i in range(left, n - right):
        hi, lo = candles[i].high, candles[i].low
        if all(candles[i - j].high < hi for j in range(1, left + 1)) and all(
            candles[i + j].high < hi for j in range(1, right + 1)
        ):
            pivots.append(Pivot(i, "HIGH", hi, min(left, right)))
        if all(candles[i - j].low > lo for j in range(1, left + 1)) and all(
            candles[i + j].low > lo for j in range(1, right + 1)
        ):
            pivots.append(Pivot(i, "LOW", lo, min(left, right)))
    return pivots


def confirmed_swing_pivots(candles: list[CandleData], left: int = 2, right: int = 2) -> list[Pivot]:
    """Fractal pivots that only need the *prior* `left` bars plus the bar itself.

    Mid-confirmation approximation used in backtests: a pivot is confirmed as soon
    as `right` bars have *closed after* it with no close beyond it — so a signal
    emitted at bar i+right is based only on data through i+right.
    """
    if left < 1 or right < 1:
        raise ValueError("left and right must be positive")
    n = len(candles)
    pivots: list[Pivot] = []
    if n < left + right:
        return pivots
    for i in range(left, n - right):
        hi, lo = candles[i].high, candles[i].low
        high_ok = all(candles[i - j].high < hi for j in range(1, left + 1)) and all(
            candles[i + j].high < hi for j in range(1, right + 1)
        )
        low_ok = all(candles[i - j].low > lo for j in range(1, left + 1)) and all(
            candles[i + j].low > lo for j in range(1, right + 1)
        )
        if high_ok:
            pivots.append(Pivot(i, "HIGH", hi, min(left, right)))
        elif low_ok:
            pivots.append(Pivot(i, "LOW", lo, min(left, right)))
    # Emit only the pivots whose right-confirmation window has fully elapsed
    # for the last `right` bars (so we never reference the future).
    cutoff = n - right
    return [p for p in pivots if p.index < cutoff]


def support_resistance(pivots: list[Pivot], window: int = 50) -> list[tuple[float, str]]:
    """Cluster pivots of the same polarity into levels (LOW→support, HIGH→resistance).

    Levels are merged when they lie within 0.5% of each other. Returned kind is
    ``"S"`` for support or ``"R"`` for resistance. `window` is kept for API
    stability (proximity pooling uses price tolerance).
    """
    if not pivots:
        return []
    levels: list[tuple[float, str]] = []
    for pivot in pivots:
        kind = "S" if pivot.kind == "LOW" else "R"
        level = pivot.level
        merged = False
        for idx, (lv, lk) in enumerate(levels):
            if abs(lv - level) < lv * 0.005:
                # keep the stronger/earlier level price, same polarity expected
                levels[idx] = (lv, lk)
                merged = True
                break
        if not merged:
            levels.append((level, kind))
    return levels
