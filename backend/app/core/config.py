"""Application settings.

All configuration comes from environment variables (or a .env file in local dev).
Never hardcode secrets here.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # --- app ---
    app_name: str = "TrendCipher"
    debug: bool = False
    public_base_url: str = "http://localhost:8000"
    api_prefix: str = "/api/v1"

    # --- security ---
    secret_key: str = "CHANGE_ME_IN_PRODUCTION_PLACEHOLDER_32_BYTES_Min"
    access_token_ttl_minutes: int = 30
    refresh_token_ttl_days: int = 14
    jwt_algorithm: str = "HS256"
    cors_origins: str = "*"

    # --- database ---
    database_url: str = "sqlite:///./trendcipher.db"

    # --- providers ---
    market_provider: str = "kraken"
    news_provider: str = "rss"
    billing_provider: str = "demo"  # none|demo|stripe (see ADR-011)
    news_feeds: str = (
        "https://cointelegraph.com/rss|CoinTelegraph,"
        "https://www.coindesk.com/arc/outboundfeeds/rss/|CoinDesk"
    )

    # --- ingestion ---
    candle_inteval_default: str = "1h"
    ingestion_loop_seconds: int = 300
    news_loop_seconds: int = 600

    # --- optional credentials (unused for public data; buyer configures) ---
    expo_access_token: str = ""
    okx_api_key: str = ""
    okx_api_secret: str = ""
    okx_passphrase: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def news_feed_list(self) -> list[tuple[str, str]]:
        feeds: list[tuple[str, str]] = []
        for entry in self.news_feeds.split(","):
            if "|" in entry:
                url, name = entry.split("|", 1)
                feeds.append((url.strip(), name.strip()))
        return feeds


settings = Settings()
