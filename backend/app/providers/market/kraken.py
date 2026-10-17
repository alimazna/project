"""Kraken REST market data adapter (primary provider).

Docs: https://docs.kraken.com/api/docs/rest-api/get-ohlc-data
Pair naming: XXBTZUSD (BTC), XETHZUSD (ETH), XRPUSD, etc.
"""

from datetime import UTC, datetime

from app.providers.base import CandleData, MarketProvider, ProviderError, TickerData

API_BASE = "https://api.kraken.com/0/public"

# Kraken names with leading 'X'/'Z' conventions for common symbols.
_ALT_PAIRS: dict[str, str] = {
    "BTC": "XBT",
    "ETH": "ETH",
    "XRP": "XRP",
    "SOL": "SOL",
    "LTC": "LTC",
    "DOT": "DOT",
    "ADA": "ADA",
    "DOGE": "DOGE",
    "LINK": "LINK",
    "MATIC": "MATIC",
    "AVAX": "AVAX",
    "UNI": "UNI",
    "ATOM": "ATOM",
    "FIL": "FIL",
    "XTZ": "XTZ",
    "ALGO": "ALGO",
    "ETC": "ETC",
    "MANA": "MANA",
    "SAND": "SAND",
    "APE": "APE",
    "GBP": "GBP",
    "JPY": "JPY",
    "EUR": "EUR",
    "USD": "USD",
    "USDC": "USDC",
    "USDT": "USDT",
}

# Kraken kline intervals -> standard interval strings accepted by our engine.
_INTERVAL_BY_MINUTES: dict[int, str] = {
    1: "1m",
    5: "5m",
    15: "15m",
    30: "30m",
    60: "1h",
    240: "4h",
    1440: "1d",
    10080: "1w",
    21600: "15d",
}

def _kraken_pair(symbol: str) -> str:
    """Map canonical BTC/USD -> Kraken XXBTZUSD."""
    base, _, quote = symbol.partition("/")
    if base in _ALT_PAIRS:
        base = _ALT_PAIRS[base]
    if quote in _ALT_PAIRS:
        quote = _ALT_PAIRS[quote]
    # Kraken format: X<base 3..4 chars><quote 3..4 chars> (USD -> ZUSD)
    if base == "XBT":
        base_code = "XBT"
    else:
        base_code = base
    return f"{base_code}{quote}"


def _interval_minutes(interval: str) -> int:
    if interval.endswith("m"):
        return int(interval[:-1])
    if interval.endswith("h"):
        return int(interval[:-1]) * 60
    if interval == "1d":
        return 1440
    if interval == "1w":
        return 10080
    raise ValueError(f"Unsupported interval for Kraken: {interval}")


class KrakenProvider(MarketProvider):
    name = "kraken"

    def fetch_klines(
        self,
        symbol: str,
        interval: str,
        *,
        limit: int = 200,
        since: datetime | None = None,
    ) -> list[CandleData]:
        minutes = _interval_minutes(interval)
        if minutes not in _INTERVAL_BY_MINUTES:
            raise ProviderError(f"Kraken does not support interval {interval}")
        params: dict = {"pair": _kraken_pair(symbol), "interval": minutes}
        if since is not None:
            params["since"] = str(int(since.timestamp()))
        resp = self._client.get(f"{API_BASE}/OHLC", params=params)
        resp.raise_for_status()
        body = resp.json()
        if body.get("error"):
            raise ProviderError(f"Kraken OHLC error: {body['error']}")

        result = body.get("result") or {}
        # key: pair name, value: list of candle arrays
        klines_raw: list = next(iter(result.values()), [])
        candles: list[CandleData] = []
        for k in klines_raw:
            ts, open_p, high, low, close, volume, *_ = k
            candles.append(
                CandleData(
                    symbol=symbol,
                    interval=interval,
                    open_time=datetime.fromtimestamp(float(ts), tz=UTC),
                    open=float(open_p),
                    high=float(high),
                    low=float(low),
                    close=float(close),
                    volume=float(volume),
                )
            )
        return candles[-limit:]

    def fetch_ticker(self, symbol: str) -> TickerData | None:
        pair = _kraken_pair(symbol)
        resp = self._client.get(f"{API_BASE}/Ticker", params={"pair": pair})
        resp.raise_for_status()
        body = resp.json()
        if body.get("error"):
            return None  # pair not tradable -> not an error worth surfacing
        result = body.get("result") or {}
        # A single-pair request returns exactly one key (e.g. XXBTZUSD).
        if len(result) != 1:
            return None
        t = next(iter(result.values()))
        # {"c": [last, ...], "h":[high, ...], "l":[...], "v":[...], "p":[...]}
        return TickerData(
            symbol=symbol,
            last_price=float(t["c"][0]),
            high_24h=float(t["h"][0]),
            low_24h=float(t["l"][0]),
            volume_24h=float(t["v"][1]),
            quote_volume_24h=None,
            change_24h_pct=None,
        )
