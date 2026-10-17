# TrendCipher — Analytical Engine

**Status:** Baseline
**Date:** 2026-10-17
**Version:** engine rule-set v0.1.0

---

## 1. Design Principles

1. **Deterministic.** For identical inputs, the engine produces identical
   outputs. No randomness, no embedded LLM in the decision path by default.
2. **Testable.** Every rule is an isolated pure function with unit tests.
3. **No future information.** Indicator and scenario calculations use **only
   closed candles** whose `close_time <= now`. The live forming candle is
   excluded or explicitly labeled `is_live: true`.
4. **Traceable.** Every scenario stores the rule version, the exact candles it
   used (count + last timestamp), and every news item it considered.
5. **Honest uncertainty.** If evidence is insufficient or contradictory, the
   engine returns an explicit non-actionable state.
6. **No profit claims.** The engine never reports a win rate or expected
   profitability. Scores are alignment scores, not calibrated probabilities.

---

## 2. Inputs

| Input | Source | Stored as |
|---|---|---|
| OHLCV candles (closed) | Market provider → DB | `candles` table |
| News articles | News provider → DB | `news_articles` table |
| Asset mapping | News classifier | `news_assets` table |
| Rule version | Backend constants | `analysis_rules` table |

---

## 3. Technical Analysis Layer

### 3.1 Indicators (deterministic, closed-candle only)

- **EMA(fast/slow)** — Exponential Moving Average; defaults fast=12, slow=26.
- **RSI(14)** — Relative Strength Index using Wilder smoothing.
- **ATR(14)** — Average True Range (percentage and absolute).
- **SMA(20/50/200)** — Simple Moving Averages.
- **Volume Z-score** — (volume − mean)/std over last N=20 closed candles.
- **Higher-high / higher-low structure** detection over a configurable window.
- **Support/resistance** — recent swing highs/lows via pivots (window k=3).
- **Multi-timeframe alignment** — compare `1h` and `4h` trend signals.

All indicators are computed in a single pass, left-to-right, **never** touching
index `i` for any value derived from candles at index `> i`.

### 3.2 Price levels

- **Entry zone:** derived from pullback to the recent structure (e.g.,
  `min(low of last N) + ATR * 0.1` .. `open area`) when trend is confirmed.
- **Take-profit targets:** cluster of (a) measured move from structure breakout,
  (b) previous swing high/low, (c) ATR multiples. Selected with **conservative
  priority** (nearest plausible target).
- **Stop-loss / invalidation:** below the confirmed structure swing (for longs)
  minus an ATR buffer; the engine refuses to emit a scenario whose risk/reward
  from the entry-zone midpoint is below a configurable minimum (default 1.2).
- **Invalidation:** a close beyond the stop level, or a stated event condition.

### 3.3 Indicator interpretation

| Signal | Condition |
|---|---|
| Trend up (1h) | `EMA12 > EMA26` and close > EMA26 and `RSI > 50` |
| Trend down (1h) | `EMA12 < EMA26` and close < EMA26 and `RSI < 50` |
| Momentum up | Recent RSI increasing over last 3 closed values and RSI in 50–70 band |
| Volume spike | Volume Z-score > +1.5 on the most recent closed candle |
| ATR expansion | ATR% > 1.5× the 14-period mean ATR% |

---

## 4. News Intelligence Layer

### 4.1 Pipeline per article

1. Extract & validate fields: title, link, published_at, retrieved_at, source.
2. Deduplicate: exact URL, then fuzzy title similarity (cosine over tokens,
   threshold 0.85). Keep the earliest published copy.
3. **Asset mapping:** tokenize normalized text and score against an asset lexicon
   (BTC, ETH, SOL, XRP, DOGE + aliases like "bitcoin", "ethereum"). Also match
   sector tags (DeFi, L2, mining, regulation, macro).
4. **Sentiment classification:** deterministic lexicon scoring (positive word
   list minus negative word list, with negation handling "not/don't/no/against").
   Output: `positive | negative | mixed | neutral` using thresholds.
5. **Relevance score** (0–100, transparent): weighted sum of asset mention
   strength, title match, recency decay, source weight. This is a **relative
   alignment score**, explicitly not a probability.
6. **Importance flags:** regulatory/macro keywords, exchange/listings,
   protocol exploits/probes increase weight on the stored `importance` field.
7. **Staleness/quality:** if `published_at - retrieved_at > 48h`, mark
   `stale_delivery`. If feed missing timestamp, mark `missing_timestamp` and apply
   retrieved_at as fallback (documented).

### 4.2 Caveats encoded in the engine

- Positive headline → **never** a bullish price signal by itself.
- News only *modulates* the technical scenario weight, per section 5.
- Classifications are stored with the classifier version so audit is possible.

---

## 5. Unified Scenario Generation

### 5.1 Evidence combination

The engine computes:

- `tech_direction ∈ {bullish, bearish, neutral}` from technical layer.
- For each mapped asset, an aggregated `news_lean ∈ {bullish, bearish, mixed, neutral, none}`
  and `news_alignment ∈ [0,1]`.

### 5.2 Decision matrix (v0.1.0)

| tech_direction | news_lean | aligned? | Scenario |
|---|---|---|---|
| bullish | bullish | yes | `BULLISH` (if structure confirms) |
| bullish | bearish | no | `CONFLICTING_EVIDENCE` |
| bullish | neutral/none | partial | `BULLISH_CONDITIONAL` — news weight low |
| bearish | bearish | yes | `BEARISH` |
| bearish | bullish | no | `CONFLICTING_EVIDENCE` |
| bearish | neutral/none | partial | `BEARISH_CONDITIONAL` |
| neutral | any | — | `NEUTRAL` |
| data insufficient | — | — | `INSUFFICIENT_DATA` |

`CONFLICTING_EVIDENCE` and `NEUTRAL` are **non-actionable** — no levels emitted.

### 5.3 Practical confirmation rules

- Trend requires ≥ 2 consecutive closed candles satisfying the direction rule.
- RSI extremes (>75 bullish-contra, <25 bearish-contra) warn against entry even
  if trend and news agree.
- A scenario from a pullback entry requires current price inside the entry zone,
  else the scenario is `SETUP_WAITING` with entry zone shown.

### 5.4 Scenario record

Each scenario persists:

```json
{
  "id": "...",
  "symbol": "BTCUSDT",
  "direction": "BULLISH",
  "timeframe": "1h",
  "status": "ACTIVE",
  "rule_version": "engine.v0.1.0",
  "created_at": "...",
  "confidence_alignment_score": 0-100,
  "entry_zone": {"low": "...", "high": "..."},
  "take_profits": [{"level": "...", "note": "..."}],
  "stop_loss": {"level": "...", "reason": "structure swing below entry"},
  "invalidation": {"condition": "...", "level": "..."},
  "risk_reward_ratio": 1.35,
  "evidence": {
    "candles_used": {"timeframe": "1h", "count": 120, "last_close_ts": "..."},
    "news_map": {"BTCUSDT": [{"id": "...", "title": "...", "link": "..."}]},
    "indicators": {"ema12": "...", "ema26": "...", "rsi14": "...", "atr_pct": "..."}
  },
  "decisions": [
    {"key": "trend", "value": "bullish", "reason": "EMA12>EMA26..."},
    {"key": "news_lean", "value": "positive", "reason": "news headline keywords"}
  ]
}
```

### 5.5 State machine

```
NEW → ACTIVE (when entry conditions met)
ACTIVE → TARGET_HIT (close ≥ tp1)
ACTIVE → STOPPED_OUT (close ≤ stop)
ACTIVE → INVALIDATED (explicit invalidation condition)
ACTIVE → EXPIRED (max lifetime exceeded)
ACTIVE → CANCELLED (rule update / manual)
```

All transitions append a `scenario_events` row (audit trail).

---

## 6. Historical Validation

### 6.1 Reproducibility

- A backtest runner replays stored closed candles through the same engine with
  `rule_version` fixed.
- Deterministic: same storage snapshot → same scenario list.

### 6.2 Leakage guards

- The runner walks candles chronologically; at index `i` only candles `<= i-1`
  exist in the engine input.
- Duplicate/overlap check: scenario windows must not double-count the same
  closed candle for the same rule+symbol.
- Fees/spread: when simulating, a configurable `taker_fee_pct` and `slippage_pct`
  (defaults 0.1% / 0.05%) are applied to entries/exits. Defaults are documented
  assumptions, not claims.
- Out-of-sample discipline: no automated tuning is run against the final
  evaluation window; we report raw outcomes only.

### 6.3 Honest reporting

- We report scenario hit/stop/miss **counts by rule version**, not "win rate" or
  "expected profit", unless a parameterized simulation is explicitly labeled as
  such with all fees and assumptions in the output.
- Historical news coverage is unavailable except for live-fetched items; the
  engine stores only what it saw at runtime and labels news evidence accordingly.

---

## 7. Testing Strategy for the Engine

Unit tests (detailed in `IMPLEMENTATION_ROADMAP.md` and enforced by CI):

1. Determinism: run engine twice on the same snapshot → identical scenario JSON.
2. No-lookahead: construct a synthetic series where candle N is a huge outlier;
   assert scenario at N−1 is unaffected.
3. Dedup idempotency: reprocessing the same news set does not create duplicates.
4. Level rules: given a known structure, entry/TP/SL exactly match documented
   rules.
5. Non-actionable states: insufficient candles → `INSUFFICIENT_DATA`;
   conflicting news/tech → `CONFLICTING_EVIDENCE`.
6. RSI/ATR/EMA edge cases: flat series, single candle, missing values.
7. Timezone: timestamps compared in UTC only.

---

## 8. Configuration (no code changes needed)

Engine thresholds live in a JSON config (`analysis/config/default.json`)
readable by admins via settings, versioned alongside the rules so scenarios stay
reproducible.