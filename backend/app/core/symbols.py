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
    # Tier 1 — core majors (verified on Kraken)
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
    SymbolInfo("BCH/USD", "BCH", "USD", "Bitcoin Cash", tier=2),
    SymbolInfo("ZEC/USD", "ZEC", "USD", "Zcash", tier=2),
    SymbolInfo("DASH/USD", "DASH", "USD", "Dash", tier=2),
    # Tier 2 — L1 / L2 platforms (verified on Kraken)
    SymbolInfo("NEAR/USD", "NEAR", "USD", "Near Protocol", tier=2),
    SymbolInfo("ICP/USD", "ICP", "USD", "Internet Computer", tier=2),
    SymbolInfo("HBAR/USD", "HBAR", "USD", "Hedera", tier=2),
    SymbolInfo("VET/USD", "VET", "USD", "VeChain", tier=2),
    SymbolInfo("EGLD/USD", "EGLD", "USD", "MultiversX", tier=2),
    SymbolInfo("FLOW/USD", "FLOW", "USD", "Flow", tier=2),
    SymbolInfo("KSM/USD", "KSM", "USD", "Kusama", tier=2),
    SymbolInfo("OP/USD", "OP", "USD", "Optimism", tier=2),
    SymbolInfo("ARB/USD", "ARB", "USD", "Arbitrum", tier=2),
    SymbolInfo("APT/USD", "APT", "USD", "Aptos", tier=2),
    SymbolInfo("SUI/USD", "SUI", "USD", "Sui", tier=2),
    SymbolInfo("IMX/USD", "IMX", "USD", "Immutable X", tier=2),
    SymbolInfo("TIA/USD", "TIA", "USD", "Celestia", tier=2),
    SymbolInfo("SEI/USD", "SEI", "USD", "Sei", tier=2),
    SymbolInfo("MINA/USD", "MINA", "USD", "Mina Protocol", tier=2),
    SymbolInfo("KAVA/USD", "KAVA", "USD", "Kava", tier=2),
    # Tier 2 — DeFi / DEX (verified on Kraken)
    SymbolInfo("AAVE/USD", "AAVE", "USD", "Aave", tier=2),
    SymbolInfo("CRV/USD", "CRV", "USD", "Curve DAO", tier=2),
    SymbolInfo("MKR/USD", "MKR", "USD", "Maker", tier=2),
    SymbolInfo("SNX/USD", "SNX", "USD", "Synthetix", tier=2),
    SymbolInfo("LDO/USD", "LDO", "USD", "Lido DAO", tier=2),
    SymbolInfo("RENDER/USD", "RENDER", "USD", "Render", tier=2),
    SymbolInfo("FET/USD", "FET", "USD", "Fetch.ai", tier=2),
    SymbolInfo("GRT/USD", "GRT", "USD", "The Graph", tier=2),
    SymbolInfo("PENDLE/USD", "PENDLE", "USD", "Pendle", tier=2),
    SymbolInfo("DYDX/USD", "DYDX", "USD", "dYdX", tier=2),
    SymbolInfo("ENS/USD", "ENS", "USD", "Ethereum Name Service", tier=2),
    SymbolInfo("1INCH/USD", "1INCH", "USD", "1inch", tier=2),
    SymbolInfo("ALCX/USD", "ALCX", "USD", "Alchemix", tier=2),
    SymbolInfo("ANKR/USD", "ANKR", "USD", "Ankr", tier=2),
    SymbolInfo("BAL/USD", "BAL", "USD", "Balancer", tier=2),
    # Tier 2 — gaming / metaverse / meme (verified on Kraken)
    SymbolInfo("SAND/USD", "SAND", "USD", "The Sandbox", tier=2),
    SymbolInfo("MANA/USD", "MANA", "USD", "Decentraland", tier=2),
    SymbolInfo("GALA/USD", "GALA", "USD", "Gala Games", tier=2),
    SymbolInfo("ENJ/USD", "ENJ", "USD", "Enjin Coin", tier=2),
    SymbolInfo("CHZ/USD", "CHZ", "USD", "Chiliz", tier=2),
    SymbolInfo("APE/USD", "APE", "USD", "ApeCoin", tier=2),
    SymbolInfo("PEPE/USD", "PEPE", "USD", "Pepe", tier=2),
    SymbolInfo("SHIB/USD", "SHIB", "USD", "Shiba Inu", tier=2),
    SymbolInfo("BONK/USD", "BONK", "USD", "Bonk", tier=2),
    SymbolInfo("WIF/USD", "WIF", "USD", "dogwifhat", tier=2),
    # Tier 2 — derived / ecosystem (verified on Kraken)
    SymbolInfo("JUP/USD", "JUP", "USD", "Jupiter", tier=2),
    SymbolInfo("INJ/USD", "INJ", "USD", "Injective", tier=2),
    SymbolInfo("PYTH/USD", "PYTH", "USD", "Pyth Network", tier=2),
    SymbolInfo("TON/USD", "TON", "USD", "Toncoin", tier=2),
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
