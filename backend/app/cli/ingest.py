"""Manual ingestion runner: python -m app.cli.ingest [--sync news|market|tickers]"""

from __future__ import annotations

import argparse
import sys

from app.db.session import SessionLocal
from app.services.ingest_runner import run_candle_sync, run_news_sync, run_ticker_sync


def main() -> int:
    parser = argparse.ArgumentParser(description="TrendCipher ingestion worker (one-shot)")
    parser.add_argument(
        "--sync",
        choices=["market", "tickers", "news"],
        default="market",
        help="Which pipeline to run (default: market = candles + tickers)",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        if args.sync == "news":
            result = run_news_sync(db)
            print(f"news: inserted={result.get('inserted')} duplicates={result.get('duplicates')}")
        elif args.sync == "tickers":
            result = run_ticker_sync(db)
            print(f"tickers: updated={result.get('tickers')} errors={result.get('errors')}")
        else:
            result = run_candle_sync(db)
            print(
                f"market: candles={result.get('candles_inserted')} "
                f"tickers={result.get('tickers')} errors={result.get('errors')}"
            )
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
