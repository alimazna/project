"""News provider registry + factory."""

from app.core.config import settings
from app.providers.base import NewsProvider
from app.providers.news.rss import RSSNewsProvider


def get_news_provider(name: str | None = None) -> NewsProvider:
    chosen = name or settings.news_provider
    if chosen == "rss":
        return RSSNewsProvider(feeds=settings.news_feed_list)
    raise ValueError(f"Unknown news provider '{chosen}'. Available: ['rss']")
