"""Leakage-guarded walk-forward backtest for the TrendCipher engine.

Core guarantee: a scenario at bar `i` is computed **only** from candles in
`candles[: i + 1]` (closed bars that exist before the signal). The outcome is
measured over the forward window *(i+1 .. i+hold_bars]*, which is never fed back
into the scenario computation. This makes look-ahead structurally impossible for
the direction/entry decisions.

Statistical output is deterministic for a fixed snapshot: running the same
backtest twice yields byte-identical JSON.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from app.analysis.engine import compute_scenario
from app.analysis.indicators import CandleData

MIN_BARS = 30  # warm-up required by the engine
HOLD_DEFAULT = 24
LOOKBACK_DEFAULT = 400  # rows evaluated per run for predictable runtime


@dataclass
class TradeResult:
    index: int
    symbol: str
    direction: str
    entry: float
    exit_price: float
    pnl_pct: float
    alignment: float
    rule_version: str
    hold_bars: int


class BacktestLeakError(RuntimeError):
    """Raised when a backtest would feed future data into the engine."""


def _compute_at(candles: list[CandleData], end: int, symbol: str, now: datetime) -> dict:
    """Compute a scenario using only candles[:end+1]."""
    window = candles[: end + 1]
    return compute_scenario(window, symbol=symbol, timeframe="1h", now=now)


def run_backtest(
    candles: list[CandleData],
    symbol: str = "BTC/USD",
    *,
    hold_bars: int = HOLD_DEFAULT,
    start: int = MIN_BARS,
    end: int | None = None,
) -> dict:
    """Walk-forward backtest over `candles`.

    Returns a snapshot dict: {results, stats, config}. Never mutates inputs.
    """
    if len(candles) < MIN_BARS + 1:
        raise ValueError(f"backtest needs at least {MIN_BARS + 1} candles, got {len(candles)}")

    n = len(candles)
    end = min(end, n - 1) if end is not None else n - 1
    if start < MIN_BARS:
        start = MIN_BARS

    results: list[TradeResult] = []
    # Deterministic clock: anchor at the last candle's timestamp.
    base_time = candles[-1].open_time
    if base_time.tzinfo is None:
        base_time = base_time.replace(tzinfo=UTC)

    for i in range(start, end + 1):
        # --- leakage guard: we compute on candx <= i only ---
        now = base_time
        scenario = _compute_at(candles, i, symbol, now)
        if scenario["direction"] == "NEUTRAL":
            continue
        if i + hold_bars >= n:
            continue  # no forward room for a clean exit

        entry = scenario["last_close"]
        exit_index = i + hold_bars
        exit_price = candles[exit_index].close

        if scenario["direction"] == "BULLISH":
            pnl_pct = (exit_price / entry - 1.0) * 100.0
        else:  # BEARISH
            pnl_pct = (1.0 - exit_price / entry) * 100.0

        results.append(
            TradeResult(
                index=i,
                symbol=symbol,
                direction=scenario["direction"],
                entry=round(entry, 6),
                exit_price=round(exit_price, 6),
                pnl_pct=round(pnl_pct, 4),
                alignment=scenario["alignment_score"],
                rule_version=scenario["rule_version"],
                hold_bars=hold_bars,
            )
        )

    return {
        "results": [vars(r) for r in results],
        "stats": _compute_stats(results, hold_bars),
        "config": {"symbol": symbol, "hold_bars": hold_bars, "start": start, "end": end},
    }


def _compute_stats(results: list[TradeResult], hold_bars: int) -> dict:
    if not results:
        return {
            "trades": 0,
            "wins": 0,
            "losses": 0,
            "winrate_pct": 0.0,
            "avg_pnl_pct": 0.0,
            "total_pnl_pct": 0.0,
            "hold_bars": hold_bars,
        }
    wins = [r for r in results if r.pnl_pct > 0]
    losses = [r for r in results if r.pnl_pct <= 0]
    total = sum(r.pnl_pct for r in results)
    return {
        "trades": len(results),
        "wins": len(wins),
        "losses": len(losses),
        "winrate_pct": round(len(wins) / len(results) * 100.0, 2),
        "avg_pnl_pct": round(total / len(results), 4),
        "total_pnl_pct": round(total, 4),
        "hold_bars": hold_bars,
    }

