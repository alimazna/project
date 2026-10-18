"""Background ingestion worker.

Runs candle/ticker sync on an interval and news sync on a longer interval.
Designed to run as its own process: python -m app.workers.ingestion
"""

from __future__ import annotations

import logging
import signal
import time

from app.core.config import settings
from app.db.session import SessionLocal
from app.services import alerts
from app.services.ingest_runner import run_candle_sync, run_news_sync

logger = logging.getLogger(__name__)


class IngestionWorker:
    def __init__(self) -> None:
        self._stopping = False
        self.last_market_at = 0.0
        self.last_news_at = 0.0

    def start(self) -> None:
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)
        self.last_market_at = time.monotonic()
        self.last_news_at = time.monotonic()
        logger.info("ingestion worker started (market=%ss news=%ss)", settings.ingestion_loop_seconds, settings.news_loop_seconds)
        while not self._stopping:
            self._tick()
            time.sleep(5)

    def _tick(self) -> None:
        now = time.monotonic()
        db = SessionLocal()
        try:
            if now - self.last_market_at >= settings.ingestion_loop_seconds:
                logger.info("running candle/ticker sync")
                result = run_candle_sync(db)
                logger.info("market sync done: %s", result)
                self.last_market_at = now
            if now - self.last_news_at >= settings.news_loop_seconds:
                logger.info("running news sync")
                result = run_news_sync(db)
                logger.info("news sync done: %s", result)
                self.last_news_at = now
            # Alert evaluation piggybacks on the market tick — cheap and keeps
            # price/scenario/news alerts live without a separate scheduler.
            alert_result = alerts.evaluate_all(db)
            if alert_result["fired"]:
                logger.info("alerts fired: %s", alert_result)
        except Exception:
            logger.exception("ingestion tick failed")
        finally:
            db.close()

    def _handle_signal(self, *_):
        logger.info("stopping ingestion worker")
        self._stopping = True


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    IngestionWorker().start()


if __name__ == "__main__":
    main()
