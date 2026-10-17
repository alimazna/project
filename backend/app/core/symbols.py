"""Canonical symbol catalog.

Symbols use the canonical BASE/QUOTE form (e.g. BTC/USD).
The catalog is provider-agnostic; each provider maps to its own naming.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SymbolInfo:
    symbol: str
    base: str
    quote: str
    display_name: str
    tier: int = 1  # 1 = core, 2 = extended


_SYMBOLS: list[SymbolInfo] = [
    SymbolInfo("BTC/USD", "BTC", "USD", "Bitcoin"),
    SymbolInfo("ETH/USD", "ETH", "USD", "Ethereum"),
    SymbolInfo("SOL/USD", "SOL", "USD", "Solana"),
    SymbolInfo("XRP/USD", "XRP", "USD", "XRP"),
    SymbolInfo("ADA/USD", "ADA", "USD", "Cardano"),
    SymbolInfo("DOGE/USD", "DOGE", "USD", "Dogecoin"),
    SymbolInfo("LINK/USD", "LINK", "USD", "Chainlink"),
    SymbolInfo("DOT/USD", "DOT", "USD", "Polkadot"),
    SymbolInfo("LTC/USD", "LTC", "USD", "Litecoin"),
    SymbolInfo("AVAX/USD", "AVAX", "USD", "Avalanche"),
    SymbolInfo("POL/USD", "POL", "USD", "Polygon"),
    SymbolInfo("UNI/USD", "UNI", "USD", "Uniswap"),
    SymbolInfo("ATOM/USD", "ATOM", "USD", "Cosmos"),
    SymbolInfo("ETC/USD", "ETC", "USD", "Ethereum Classic"),
    SymbolInfo("XTZ/USD", "XTZ", "USD", "Tezos"),
    SymbolInfo("ALGO/USD", "ALGO", "USD", "Algorand"),
    SymbolInfo("FIL/USD", "FIL", "USD", "Filecoin"),
    # OKX USD-quoted extras (Kraken often quotes against USDT only)
    SymbolInfo("OP/USD", "OP", "USD", "Optimism", tier=2),
    SymbolInfo("ARB/USD", "ARB", "USD", "Arbitrum", tier=2),
    SymbolInfo("APT/USD", "APT", "USD", "Aptos", tier=2),
    SymbolInfo("SUI/USD", "SUI", "USD", "Sui", tier=2),
]

_DEFAULT_QUOTES = {"USD", "USDT", "USDC"}


def default_symbols(tiers: set[int] | None = None, quote: str | None = None) -> list[SymbolInfo]:
    if tiers is None:
        tiers = {1}
    return [
        s
        for s in _SYMBOLS
        if s.tier in tiers and (quote is None or s.quote == quote)
    ]


def symbol_catalog() -> dict[str, SymbolInfo]:
    return {s.symbol: s for s in _SYMBOLS}


def get_symbol_info(symbol: str) -> SymbolInfo | None:
    return symbol_catalog().get(symbol)
