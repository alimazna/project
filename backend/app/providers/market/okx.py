"""OKX REST market data adapter (secondary provider).

Docs: https://www.okx.com/docs-v5/en/#rest-api-market-data-get-candlesticks
Instrument ids look like BTC-USDT.
"""

from datetime import UTC, datetime

from app.providers.base import CandleData, MarketProvider, ProviderError, TickerData

API_BASE = "https://www.okx.com/api/v5/market"


def _inst_id(symbol: str) -> str:
    """OKX quotes against USDT/USDC (no USD pairs). USD -> USDT proxy."""
    base, quote = symbol.split("/", 1)
    if quote == "USD":
        quote = "USDT"
    return f"{base}-{quote}"


def _parse_time(value: str) -> datetime:
    # OKX returns ms epoch as string.
    return datetime.fromtimestamp(int(value) / 1000, tz=UTC)


class OKXProvider(MarketProvider):
    name = "okx"

    def fetch_klines(
        self,
        symbol: str,
        interval: str,
        *,
        limit: int = 200,
        since: datetime | None = None,
    ) -> list[CandleData]:
        bar = _okx_bar(interval)
        params: dict = {"instId": _inst_id(symbol), "bar": bar, "limit": str(limit)}
        if since is not None:
            params["after"] = str(int(since.timestamp() * 1000))
        resp = self._client.get(f"{API_BASE}/candles", params=params)
        resp.raise_for_status()
        body = resp.json()
        if body.get("code") != "0":
            raise ProviderError(f"OKX candles error: {body.get('msg')}")

        rows = body.get("data") or []
        # OKX returns newest-first: [ts, o, h, l, c, vol, vol_ccy, ...]
        candles: list[CandleData] = []
        for row in sorted(rows, key=lambda r: int(r[0])):  # chronological
            ts, open_p, high, low, close_p, vol, *_ = row
            candles.append(
                CandleData(
                    symbol=symbol,
                    interval=interval,
                    open_time=_parse_time(ts),
                    open=float(open_p),
                    high=float(high),
                    low=float(low),
                    close=float(close_p),
                    volume=float(vol),
                )
            )
        return candles[-limit:]

    def fetch_ticker(self, symbol: str) -> TickerData | None:
        resp = self._client.get(f"{API_BASE}/ticker", params={"instId": _inst_id(symbol)})
        resp.raise_for_status()
        body = resp.json()
        if body.get("code") != "0" or not body.get("data"):
            return None
        d = body["data"][0]
        last = d.get("last")
        if last is None:
            return None
        return TickerData(
            symbol=symbol,
            last_price=float(last),
            high_24h=float(d.get("high24h") or 0) or None,
            low_24h=float(d.get("low24h") or 0) or None,
            volume_24h=float(d.get("vol24h") or 0) or None,
            quote_volume_24h=float(d.get("volCcy24h") or 0) or None,
            change_24h_pct=None,
        )


def _okx_bar(interval: str) -> str:
    mapping: dict[str, str] = {
        "1m": "1m",
        "5m": "5m",
        "15m": "15m",
        "30m": "30m",
        "1h": "1H",
        "4h": "4H",
        "1d": "1D",
        "1w": "1W",
    }
    if interval not in mapping:
        raise ProviderError(f"OKX does not support interval {interval}")
    return mapping[interval]
