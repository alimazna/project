"""Provider contracts shared by market data and news providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

import httpx

DEFAULT_TIMEOUT = httpx.Timeout(15.0, connect=10.0)


class ProviderError(RuntimeError):
    """Raised when a provider fails to return usable data."""


@dataclass(frozen=True)
class CandleData:
    symbol: str  # canonical symbol, e.g. "BTC/USD"
    interval: str  # e.g. "1h"
    open_time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class TickerData:
    symbol: str
    last_price: float
    high_24h: float | None = None
    low_24h: float | None = None
    volume_24h: float | None = None
    quote_volume_24h: float | None = None
    change_24h_pct: float | None = None


class MarketProvider(ABC):
    """Adapters return normalized CandleData/TickerData, regardless of upstream."""

    name: str = "market"

    def __init__(self, *, timeout: httpx.Timeout = DEFAULT_TIMEOUT) -> None:
        self._client = httpx.Client(timeout=timeout, follow_redirects=True)

    @abstractmethod
    def fetch_klines(
        self,
        symbol: str,
        interval: str,
        *,
        limit: int = 200,
        since: datetime | None = None,
    ) -> list[CandleData]:
        """Fetch closed candles. `symbol` is canonical (e.g. BTC/USD)."""

    @abstractmethod
    def fetch_ticker(self, symbol: str) -> TickerData | None:
        """Fetch latest ticker. Returns None if the pair is not tradable."""

    def close(self) -> None:
        self._client.close()


class NewsProvider(ABC):
    """Adapters return normalized news entries from a single source."""

    name: str = "news"

    @abstractmethod
    def fetch(self) -> list[dict]:
        """Return raw normalized news items.

        Each item contains: source, url, title, summary (optional),
        author (optional), published_at (datetime | None).
        """
