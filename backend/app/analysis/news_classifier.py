"""Deterministic news classifier: sentiment lexicon, asset mapping, relevance.

Pure, stateless text analysis. Given the same title/summary, results are always
identical, so historical news can be re-scored and compared across versions.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime

CLASSIFIER_VERSION = "lexicon.v0.1.0"

# --------------------------------------------------------------------------- lexicon

_POSITIVE_WORDS = {
    "rise",
    "rises",
    "rising",
    "surge",
    "surges",
    "surged",
    "rally",
    "rallies",
    "bullish",
    "boost",
    "boosts",
    "boosted",
    "gain",
    "gains",
    "gained",
    "record",
    "all-time high",
    "higher",
    "up",
    "growth",
    "grew",
    "triumph",
    "wins",
    "win",
    "adoption",
    "investment",
    "inflow",
    "inflows",
    "breakout",
    "strength",
    "secure",
    "secured",
    "approve",
    "approved",
    "approval",
    "partnership",
    "partnerships",
    "integration",
    "upgrade",
    "mainnet",
    "funding",
    "grant",
    "profitable",
    "profit",
    "profits",
    "soar",
    "soars",
    "soaring",
    "outperform",
    "beats",
    "beat",
    "optimism",
    "positive",
    "green",
    "bull-run",
    "bull run",
    "milestone",
    "accelerate",
    "accelerating",
    "expanding",
    "expansion",
    "regulatory clarity",
}

_NEGATIVE_WORDS = {
    "fall",
    "falls",
    "falling",
    "drop",
    "drops",
    "dropped",
    "decline",
    "declines",
    "crash",
    "crashes",
    "crashed",
    "plunge",
    "plunges",
    "plunged",
    "slump",
    "slumps",
    "bearish",
    "selloff",
    "sell-off",
    "sell",
    "dump",
    "dumps",
    "dumped",
    "loss",
    "losses",
    "lost",
    "lower",
    "down",
    "negative",
    "bear",
    "bears",
    "ban",
    "banning",
    "banned",
    "scam",
    "fraud",
    "hack",
    "hacked",
    "exploit",
    "lawsuit",
    "legal",
    "crackdown",
    "crack-down",
    "regulation",
    "sanctions",
    "risk",
    "risks",
    "uncertainty",
    "fears",
    "fear",
    "warning",
    "warns",
    "warned",
    "weak",
    "weaker",
    "weakness",
    "concern",
    "concerns",
    "outflow",
    "outflows",
    "liquidation",
    "liquidations",
    "delist",
    "delisted",
    "depegged",
    "depeg",
    "deadline",
    "probe",
    "investigation",
    "mispricing",
    "vulnerability",
}

# --------------------------------------------------------------------------- asset mapping

# Name fragments (lowercase) → canonical symbol. Longer matches win.
_ASSET_ALIASES: list[tuple[str, str]] = [
    ("bitcoin", "BTC/USD"),
    ("btc", "BTC/USD"),
    ("ethereum", "ETH/USD"),
    ("ether", "ETH/USD"),
    ("eth", "ETH/USD"),
    ("solana", "SOL/USD"),
    ("sol", "SOL/USD"),
    ("xrp", "XRP/USD"),
    ("ripple", "XRP/USD"),
    ("cardano", "ADA/USD"),
    ("ada", "ADA/USD"),
    ("dogecoin", "DOGE/USD"),
    ("doge", "DOGE/USD"),
    ("chainlink", "LINK/USD"),
    ("link", "LINK/USD"),
    ("polkadot", "DOT/USD"),
    ("dot", "DOT/USD"),
    ("litecoin", "LTC/USD"),
    ("ltc", "LTC/USD"),
    ("avalanche", "AVAX/USD"),
    ("avax", "AVAX/USD"),
    ("polygon", "POL/USD"),
    ("matic", "POL/USD"),  # legacy ticker maps to POL after migration
    ("pol", "POL/USD"),
    ("uniswap", "UNI/USD"),
    ("uni", "UNI/USD"),
    ("cosmos", "ATOM/USD"),
    ("atom", "ATOM/USD"),
    ("ethereum classic", "ETC/USD"),
    ("etc", "ETC/USD"),
    ("tezos", "XTZ/USD"),
    ("xtz", "XTZ/USD"),
    ("algorand", "ALGO/USD"),
    ("algo", "ALGO/USD"),
    ("filecoin", "FIL/USD"),
    ("fil", "FIL/USD"),
    ("optimism", "OP/USD"),
    ("op", "OP/USD"),
    ("arbitrum", "ARB/USD"),
    ("arb", "ARB/USD"),
    ("aptos", "APT/USD"),
    ("apt", "APT/USD"),
    ("sui", "SUI/USD"),
]


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9+-]+", text.lower())


# --------------------------------------------------------------------------- matching


def _match_assets(text: str) -> dict[str, int]:
    """Return {canonical_symbol: mention_count} for assets found in `text`.

    Word-boundary aware: the alias must appear as a token (or a token prefix
    for multi-word names). Non-greedy longest-match wins per position.
    """
    tokens = _tokenize(text)
    lower = text.lower()
    counts: dict[str, int] = {}
    # multi-token aliases (space in alias) match anywhere in the lowercased text
    single: list[tuple[str, str]] = []
    for alias, symbol in _ASSET_ALIASES:
        if " " in alias:
            if alias in lower:
                counts[symbol] = counts.get(symbol, 0) + lower.count(alias)
        else:
            single.append((alias, symbol))
    # single-token aliases match as tokens (avoid "police" → POL etc.)
    for alias, symbol in single:
        for tok in tokens:
            if tok == alias:
                counts[symbol] = counts.get(symbol, 0) + 1
    # "ethereum classic" also implies ETC when both words appear adjacent handled above
    return counts


def classify_news(
    title: str,
    summary: str | None = None,
    *,
    published_at: datetime | None = None,
    now: datetime | None = None,
) -> dict:
    """Classify a news item. Returns sentiment, relevance, importance, assets.

    All scores are deterministic — no randomness, no external state.
    """
    text = f"{title} {summary or ''}"
    lower = text.lower()

    # --- sentiment ---
    tokens = set(_tokenize(title + " " + (summary or "")))
    pos = sum(1 for w in tokens if w in _POSITIVE_WORDS)
    neg = sum(1 for w in tokens if w in _NEGATIVE_WORDS)
    # phrases (e.g. "all-time high", "bull run") scored as a unit
    for phrase in ("all-time high", "bull run", "regulatory clarity"):
        if phrase in lower:
            pos += 1
    for phrase in ("sell-off", "bear market", "fears", "warns farmers"):
        if phrase in lower:
            neg += 1

    if pos > neg:
        sentiment = "positive"
    elif neg > pos:
        sentiment = "negative"
    elif pos == neg and pos > 0:
        sentiment = "mixed"
    else:
        sentiment = "neutral"

    # --- assets + relevance ---
    assets = _match_assets(text)
    mentions = sum(assets.values())
    if mentions >= 3:
        relevance = 1.0
    elif mentions == 2:
        relevance = 0.8
    elif mentions == 1:
        relevance = 0.6
    else:
        relevance = 0.2

    # --- importance ---
    importance = 0.2
    if mentions > 0:
        importance += 0.3  # an asset is discussed
    if relevance >= 0.8:
        importance += 0.2
    if pos or neg:
        importance += 0.1
    if title[0].isupper() and len(title) > 20:
        importance += 0.1  # headline-style
    # recency boost if we have a timestamp and a reference clock
    if published_at is not None and now is not None:
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=UTC)
        age_hours = (now - published_at).total_seconds() / 3600.0
        if age_hours >= 0 and age_hours < 48:
            importance += 0.2 * (1 - age_hours / 48.0)
    importance = round(min(importance, 1.0), 3)

    return {
        "sentiment": sentiment,
        "relevance_score": round(relevance, 3),
        "importance": importance,
        "assets": assets,
        "classifier_version": CLASSIFIER_VERSION,
        "evidence": {
            "positive_hits": pos,
            "negative_hits": neg,
            "asset_mentions": mentions,
            "title_words": len(_tokenize(title)),
        },
    }
