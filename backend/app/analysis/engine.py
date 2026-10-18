"""TrendCipher analytical engine — deterministic decision matrix + scenario production.

Combines technical indicators and news sentiment into a single, explainable
scenario object with full evidence. Purely deterministic given identical candles
and news: same inputs → same scenario.

Signal aggregation is a weighted decision matrix:

    alignment_score = Σ(weight_i * vote_i) / Σ(weight_i)        ∈ [-1, +1]

Dictionary mapping of vote → direction:

    alignment_score ≥  +0.33  → BULLISH
    alignment_score ≤  -0.33  → BEARISH
    otherwise                → NEUTRAL (non-actionable)
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.analysis.indicators import (
    CandleData,
    atr,
    ema,
    rsi,
    volume_zscore,
)
from app.analysis.news_classifier import CLASSIFIER_VERSION, classify_news

RULE_VERSION = "matrix.v0.1.0"

# Decision-matrix parameterisation. All knobs live here so rule versions can be
# audited and compared without touching code paths.
_RULES: dict[str, Any] = {
    "trend_ema": {"fast": 12, "slow": 26, "weight": 0.25},
    "momentum_rsi": {
        "period": 14,
        "oversold": 30,
        "overbought": 70,
        "cap_extreme_high": 85,  # beyond → trend-continuation, not fade
        "cap_extreme_low": 15,  # below → downtrend-continuation, not bounce
        "weight": 0.20,
    },
    "volatility_atr": {"period": 14, "weight": 0.10},
    "volume_z": {"period": 20, "spike": 1.5, "weight": 0.15},
    "structure": {"left": 2, "right": 2, "weight": 0.15},
}

_NEWS_WEIGHT = 0.15


def _require_len(candles: list[CandleData], n: int) -> None:
    if len(candles) < n:
        raise ValueError(f"need at least {n} candles, got {len(candles)}")


def _float_or(x: float | None, default: float) -> float:
    return default if x is None else float(x)


def _vote(score: float, threshold: float = 0.0) -> float:
    """Map a continuous score to a directional vote in +1/0/-1."""
    if score > threshold * 1.0:
        return 1.0
    if score < -abs(threshold):
        return -1.0
    return 0.0


def _evidence_from_decisions(decisions: list[dict]) -> dict:
    """Condense the per-signal decisions into an evidence summary."""
    votes = [d["vote"] for d in decisions if d.get("vote") in (-1.0, 0.0, 1.0)]
    return {
        "signals_evaluated": len(decisions),
        "bullish": sum(1 for v in votes if v > 0),
        "bearish": sum(1 for v in votes if v < 0),
        "neutral": sum(1 for v in votes if v == 0),
        "weighted_alignment": round(sum(d["aligned"] for d in decisions), 4),
    }


def compute_scenario(
    candles: list[CandleData],
    *,
    news: list[dict] | None = None,
    symbol: str = "BTC/USD",
    timeframe: str = "1h",
    now: datetime | None = None,
) -> dict:
    """Compute a deterministic scenario from candles (+ optional scored news).

    Returns the scenario payload (ready for the Scenario model / API).
    """
    now = now or datetime.now(UTC)
    _require_len(candles, 30)  # warm-up for EMA-26 + ATR-14 + pivots

    closes = [c.close for c in candles]
    last_close = closes[-1]

    # --- technical signals -------------------------------------------------
    decisions: list[dict] = []

    fast_ema = ema(closes, _RULES["trend_ema"]["fast"])
    slow_ema = ema(closes, _RULES["trend_ema"]["slow"])
    f, s = fast_ema[-1], slow_ema[-1]
    if f is not None and s is not None:
        gap = (f - s) / s
        vote = _vote(gap, 0.001)
        weight = _RULES["trend_ema"]["weight"]
        decisions.append(
            {
                "signal": "ema_trend",
                "vote": vote,
                "weight": weight,
                "aligned": round(vote * weight, 4),
                "value": {"fast": round(f, 6), "slow": round(s, 6), "gap_pct": round(gap * 100, 3)},
                "reason": (
                    "price above fast EMA over slow EMA (uptrend)"
                    if vote > 0
                    else (
                        "price below fast EMA over slow EMA (downtrend)"
                        if vote < 0
                        else "EMAs converged — no trend"
                    )
                ),
            }
        )

    r = rsi(closes, _RULES["momentum_rsi"]["period"])[-1]
    if r is not None:
        w = _RULES["momentum_rsi"]["weight"]
        ob = _RULES["momentum_rsi"]["overbought"]
        os = _RULES["momentum_rsi"]["oversold"]
        cap_hi = _RULES["momentum_rsi"]["cap_extreme_high"]
        cap_lo = _RULES["momentum_rsi"]["cap_extreme_low"]
        if r >= cap_hi:
            # Extremely stretched momentum = continuation (strong trend), not fade.
            vote = 1.0
            reason = f"RSI {r:.1f} extremely overbought (≥{cap_hi}) — momentum continuation"
        elif r >= ob:
            vote = -1.0  # classic overbought → fade
            reason = f"RSI {r:.1f} overbought (≥{ob}) — exhaustion risk"
        elif r <= cap_lo:
            # Deeply oversold = continuation of the down-move, not a bounce.
            vote = -1.0
            reason = f"RSI {r:.1f} extremely oversold (≤{cap_lo}) — momentum continuation down"
        elif r <= os:
            vote = 1.0  # oversold → bounce
            reason = f"RSI {r:.1f} oversold (≤{os})"
        else:
            vote = 0.0
            reason = f"RSI {r:.1f} neutral zone"
        regime = (
            "continuation_up"
            if r >= cap_hi
            else (
                "continuation_down"
                if r <= cap_lo
                else ("fade_overbought" if r >= ob else ("fade_oversold" if r <= os else "neutral"))
            )
        )
        decisions.append(
            {
                "signal": "rsi_momentum",
                "vote": vote,
                "weight": w,
                "aligned": round(vote * w, 4),
                "value": {"rsi": round(r, 3), "regime": regime},
                "reason": reason,
            }
        )

    a = atr(candles, _RULES["volatility_atr"]["period"])[-1]
    if a is not None and a > 0:
        w = _RULES["volatility_atr"]["weight"]
        vol_ratio = a / last_close
        # High volatility is not directional by itself: contribute only weight to
        # amplify existing confluence by raising alignment influence.
        decisions.append(
            {
                "signal": "volatility_regime",
                "vote": 0.0,
                "weight": w,
                "aligned": 0.0,
                "value": {"atr": round(a, 6), "atr_pct": round(vol_ratio * 100, 3)},
                "reason": f"ATR {a:.2f} ({vol_ratio * 100:.1f}% of price) — sizing context",
            }
        )

    zv = volume_zscore(candles, _RULES["volume_z"]["period"])[-1]
    if zv is not None:
        w = _RULES["volume_z"]["weight"]
        threshold = _RULES["volume_z"]["spike"]
        if zv >= threshold:
            vote = 1.0 if f is not None and s is not None and f > s else -1.0
            reason = f"volume z-score {zv:.2f} ≥ {threshold}, confirming {'trend' if vote > 0 else 'down-move'}"
        elif zv <= -threshold:
            vote = 0.0
            reason = f"volume z-score {zv:.2f} unusually low — exhaustion watch"
        else:
            vote = 0.0
            reason = f"volume z-score {zv:.2f} within normal range"
        decisions.append(
            {
                "signal": "volume_confirm",
                "vote": vote,
                "weight": w,
                "aligned": round(vote * w, 4),
                "value": {"z": round(zv, 3)},
                "reason": reason,
            }
        )

    # structure: price vs recent swing-turned-levels
    from app.analysis.indicators import confirmed_swing_pivots, support_resistance

    pivots = confirmed_swing_pivots(
        candles, _RULES["structure"]["left"], _RULES["structure"]["right"]
    )
    levels = support_resistance(pivots)
    if levels:
        nearest_support = min((lv for lv, k in levels if k == "S"), default=None)
        nearest_res = min((lv for lv, k in levels if k == "R" and lv > last_close), default=None)
        w = _RULES["structure"]["weight"]
        # Distance to nearest S/R as a vote (-1 below S, +1 above R, else 0)
        if nearest_support is not None and last_close < nearest_support:
            vote = -1.0
            reason = f"price {last_close:.2f} broke below support {nearest_support:.2f}"
        elif nearest_res is not None and last_close > nearest_res:
            vote = 1.0
            reason = f"price {last_close:.2f} broke above resistance {nearest_res:.2f}"
        else:
            vote = 0.0
            reason = f"price inside {nearest_support or 'n/a'}–{nearest_res or 'n/a'} range"
        decisions.append(
            {
                "signal": "structure_levels",
                "vote": vote,
                "weight": w,
                "aligned": round(vote * w, 4),
                "value": {
                    "nearest_support": round(nearest_support, 4) if nearest_support else None,
                    "nearest_resistance": round(nearest_res, 4) if nearest_res else None,
                    "pivots": len(pivots),
                },
                "reason": reason,
            }
        )
    else:
        decisions.append(
            {
                "signal": "structure_levels",
                "vote": 0.0,
                "weight": _RULES["structure"]["weight"],
                "aligned": 0.0,
                "value": {"pivots": 0, "note": "no confirmed levels yet"},
                "reason": "no confirmed swing levels available",
            }
        )

    # --- news sentiment signal --------------------------------------------
    news_vote_total = 0.0
    news_items_scored: list[dict] = []
    if news:
        relevant = [n for n in news if n.get("relevance_score", 0) >= 0.6]
        if relevant:
            scores = [n["sentiment"] for n in relevant]
            pos = sum(1 for x in scores if x in ("positive", "mixed"))
            neg = sum(1 for x in scores if x in ("negative", "mixed"))
            # Vote sign by majority; magnitude scales with consensus so a flow of
            # agreeing articles has outsized influence while a single article
            # only nudges the matrix.
            if pos > neg:
                news_vote_total = min(1.0, 0.33 * (pos - neg))
            elif neg > pos:
                news_vote_total = -min(1.0, 0.33 * (neg - pos))
            else:
                news_vote_total = 0.0
            # Sort deterministically so the evidence payload is independent of
            # the caller's ordering.
            news_items_scored = sorted(
                (
                    {
                        "url": n.get("url"),
                        "sentiment": n["sentiment"],
                        "relevance": n.get("relevance_score", 0),
                        "importance": n.get("importance", 0),
                    }
                    for n in relevant
                ),
                key=lambda x: (x["url"] or "", x["sentiment"], x["importance"]),
            )
    if news_items_scored:
        decisions.append(
            {
                "signal": "news_sentiment",
                "vote": news_vote_total,
                "weight": _NEWS_WEIGHT,
                "aligned": round(news_vote_total * _NEWS_WEIGHT, 4),
                "value": {"scored_articles": len(news_items_scored), "articles": news_items_scored},
                "reason": f"news lean {'bullish' if news_vote_total > 0 else ('bearish' if news_vote_total < 0 else 'neutral')}",
            }
        )
    else:
        decisions.append(
            {
                "signal": "news_sentiment",
                "vote": 0.0,
                "weight": _NEWS_WEIGHT,
                "aligned": 0.0,
                "value": {"scored_articles": 0},
                "reason": "no news scoring available / all below relevance 0.6",
            }
        )

    # --- aggregate ---------------------------------------------------------
    total_weight = sum(d["weight"] for d in decisions) or 1.0
    alignment = sum(d["aligned"] for d in decisions) / total_weight
    alignment = round(max(-1.0, min(1.0, alignment)), 4)

    if alignment >= 0.33:
        direction = "BULLISH"
    elif alignment <= -0.33:
        direction = "BEARISH"
    else:
        direction = "NEUTRAL"

    # entry / stop / targets from recent structure when direction set
    entry_low = entry_high = stop_loss = None
    take_profits: list[float] = []
    if direction != "NEUTRAL" and len(candles) >= 5:
        atr_val = a or (atr(candles, _RULES["volatility_atr"]["period"])[-1] or last_close * 0.02)
        if direction == "BULLISH":
            entry_low = round(last_close * 0.995, 6)
            entry_high = round(last_close * 1.005, 6)
            stop_loss = round(last_close - 1.5 * atr_val, 6)
            take_profits = [
                round(last_close + 1.0 * atr_val, 6),
                round(last_close + 2.0 * atr_val, 6),
            ]
        else:
            entry_low = round(last_close * 0.995, 6)
            entry_high = round(last_close * 1.005, 6)
            stop_loss = round(last_close + 1.5 * atr_val, 6)
            take_profits = [
                round(last_close - 1.0 * atr_val, 6),
                round(last_close - 2.0 * atr_val, 6),
            ]
        risk = abs(last_close - stop_loss)
        reward = abs(take_profits[-1] - last_close)
        risk_reward = round(reward / risk, 2) if risk > 0 else None
    else:
        risk_reward = None

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "direction": direction,
        "status": "NEW",
        "alignment_score": alignment,
        "rule_version": RULE_VERSION,
        "news_classifier_version": CLASSIFIER_VERSION,
        "last_close": round(last_close, 6),
        "risk_reward": risk_reward,
        "entry_low": entry_low,
        "entry_high": entry_high,
        "stop_loss": stop_loss,
        "take_profits": take_profits,
        "invalidation": (
            {
                "close_above": round(
                    entry_high + 1.0 * (atr_val if direction != "NEUTRAL" else (last_close * 0.02)),
                    6,
                )
            }
            if direction == "BEARISH"
            else {
                "close_below": round(
                    entry_low - 1.0 * (atr_val if direction != "NEUTRAL" else (last_close * 0.02)),
                    6,
                )
            }
            if direction == "BULLISH"
            else {}
        ),
        "decisions": decisions,
        "evidence": _evidence_from_decisions(decisions),
        "generated_at": now.isoformat(),
        "expiry_at": None,
    }


def enrich_news_classification(item: dict) -> dict:
    """Score/classify a news row into sentiment, assets, relevance, importance.

    Deterministic wrapper around `classify_news` that keeps the schema the API
    and ingestion layer already use.
    """
    raw = classify_news(
        item.get("title") or "",
        item.get("summary"),
        published_at=item.get("published_at"),
    )
    return {
        "sentiment": raw["sentiment"],
        "relevance_score": raw["relevance_score"],
        "importance": raw["importance"],
        "assets": list(raw["assets"].keys()),
        "classifier_version": raw["classifier_version"],
    }
