"""RSS news adapter using feedparser (CoinTelegraph, CoinDesk, ...).

Handles:
- missing/invalid timestamps (marks missing_timestamp=True, does not drop)
- UTF-8 titles (em-dash test cases)
- utm tracking params stripped
"""

from calendar import timegm
from datetime import UTC, datetime, timedelta

import feedparser

from app.providers.base import NewsProvider, ProviderError

_TRACKING_PARAMS = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content"}


def _strip_utm(url: str) -> str:
    if "utm_" not in url:
        return url
    base, _, query = url.partition("?")
    kept = [(k, v) for k, v in (p.split("=", 1) for p in query.split("&")) if k not in _TRACKING_PARAMS]
    if not kept:
        return base
    return base + "?" + "&".join(f"{k}={v}" for k, v in kept)


def _parse_published(entry: dict) -> tuple[datetime | None, bool]:
    """Return (datetime|None, missing_flag) from a feedparser entry."""
    parsed_tuple = entry.get("published_parsed")
    if not parsed_tuple:
        return None, True
    dt = datetime.fromtimestamp(timegm(parsed_tuple), tz=UTC)
    # Guard against wildly future timestamps (a known feed quirk).
    if dt > datetime.now(UTC) + timedelta(days=2):
        return None, True
    return dt, False


class RSSNewsProvider(NewsProvider):
    name = "rss"

    def __init__(self, feeds: list[tuple[str, str]] | None = None) -> None:
        self.feeds = feeds or [
            ("https://cointelegraph.com/rss", "CoinTelegraph"),
            ("https://www.coindesk.com/arc/outboundfeeds/rss/", "CoinDesk"),
        ]

    def fetch(self) -> list[dict]:
        items: list[dict] = []
        for url, source in self.feeds:
            parsed = feedparser.parse(url)
            if parsed.get("bozo") and not parsed.entries:
                raise ProviderError(f"RSS feed failed: {url} ({parsed.get('bozo_exception')})")
            for entry in parsed.entries:
                published, missing = _parse_published(entry)
                link = _strip_utm(entry.get("link", ""))
                items.append(
                    {
                        "source": source,
                        "url": link,
                        "title": entry.get("title", ""),
                        "summary": entry.get("summary", "")[:2000] or None,
                        "author": entry.get("author"),
                        "published_at": published,
                        "missing_timestamp": missing,
                    }
                )
        return items
