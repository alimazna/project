"""Market provider registry + factory."""

from app.providers.base import MarketProvider
from app.providers.market.kraken import KrakenProvider
from app.providers.market.okx import OKXProvider

_PROVIDERS: dict[str, type[MarketProvider]] = {
    KrakenProvider.name: KrakenProvider,
    OKXProvider.name: OKXProvider,
}


def get_market_provider(name: str) -> MarketProvider:
    try:
        return _PROVIDERS[name]()
    except KeyError:
        raise ValueError(
            f"Unknown market provider '{name}'. Available: {sorted(_PROVIDERS)}"
        ) from None


def list_providers() -> list[str]:
    return sorted(_PROVIDERS)
