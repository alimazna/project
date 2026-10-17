# TrendCipher — Data Providers and Licensing

**Status:** Baseline
**Date checked:** 2026-10-17
**Scope:** Every external data source, its interface, its usage terms, and the
legal distinction between accessing, displaying, storing, exporting, and reselling
data.

> **Legal disclaimer:** This document records factual observations and provider
> statements. It is **not legal advice**. A buyer should re-verify terms before
> commercial resale of data. Where terms are ambiguous we say so explicitly.

---

## 1. Data-access vs data-resale — the distinction

A free public API is **not** automatically a license to redistribute or resell the
data. This product distinguishes four tiers:

| Tier | Example activity | Typically allowed by public exchange APIs | Typical restriction |
|---|---|---|---|
| Access for personal use | Reading candles/tickers to display to the operator | Usually yes | Rate limits |
| Display to end users | Showing prices in a SaaS UI to subscribers | Usually tolerated at display-only level, but **seek explicit terms** | May require quoting terms |
| Storage / archival | Persisting candles/news in a database for the app's operation | Commonly permitted within terms, but watch caching clauses | Binance restricts "data feeding/streaming" and profit from market data |
| **Resale / redistribution** | Selling a data feed, API, or derivative data product to third parties | **Generally requires explicit written permission** | Often prohibited |

TrendCipher's default design:

- Fetches market data **at runtime** from public endpoints for **display and
  analysis** in the product the buyer operates.
- Persists normalized candles for the operator's own app functionality.
- Does **not** ship a separate "data feed" product nor resell raw market data.
- Buyers must still verify the terms of whichever provider they configure.

---

## 2. Live connectivity verification (2026-10-17)

All checks were performed from the OpenHands development environment on
**2026-10-17** with unauthenticated `GET` requests.

| Provider | Endpoint tested | Result |
|---|---|---|
| **Binance** | `/api/v3/klines?symbol=BTCUSDT&interval=1h` | ❌ HTTP 200 body: "Service unavailable from a restricted location" (geo-restricted from this environment) |
| **Bybit** | `api.bybit.com/v5/market/time` | ❌ HTTP 403 "blocked from your country" (CloudFront geo-block) |
| **Kraken** | `api.kraken.com/0/public/OHLC?pair=XBTUSD&interval=60` | ✅ 200, real OHLC data returned |
| **Coinbase** | `api.exchange.coinbase.com/products/BTC-USD/candles?granularity=3600` | ✅ 200, real data |
| **OKX** | `www.okx.com/api/v5/market/ticker?instId=BTC-USDT` | ✅ 200 `code:0`, real data |
| **KuCoin** | `api.kucoin.com/api/v1/timestamp` | ✅ 200, real data |
| **CoinGecko** | `api.coingecko.com/api/v3/ping`, `/simple/price`, `/search/trending` | ✅ 200, real data |
| **CoinTelegraph RSS** | `cointelegraph.com/rss` | ✅ 200, valid RSS 2.0 |
| **CoinDesk RSS** | `coindesk.com/arc/outboundfeeds/rss/` | ⚠️ HTTP 308 redirect (adapter must follow redirects) |

---

## 3. Primary market-data provider: Kraken

### Interface (public REST)

- Base: `https://api.kraken.com/0/public`
- Key endpoints:
  - `GET /public/Time` — server time
  - `GET /public/Assets` — asset metadata
  - `GET /public/AssetPairs` — trading pair metadata
  - `GET /public/Ticker` — last price, 24h volume, VWAP, high/low/open
  - `GET /public/OHLC?pair=XBTUSD&interval=5` — OHLCV candle history
- Candle intervals: minutes `1,5,15,30,60,240,1440,10080,21600`.
- No API key required for public endpoints.
- Rate limits: Kraken publishes per-endpoint rate limits; public market data is
  IP-based. Adapter implements exponential backoff and marks throttling events.
- Notes: candle history endpoint returns only ~720 of the most recent candles per
  request (documented behavior). For deeper history the `since` parameter is
  paged; adapter paginates.

### Usage terms (observed)

- Public market data requires no authentication.
- The Kraken Global Terms of Service govern use; they include data-protection and
  acceptable-use clauses. Terms must be re-checked by a buyer contemplating
  commercial redistribution. Kraken's own docs state public endpoints "require no
  key" for market data use cases.
- **Status: permitted use for display/analysis assumed; resale requires explicit
  verification.**

---

## 4. Fallback market-data provider: OKX

### Interface (public V5)

- Base: `https://www.okx.com/api/v5`
- Key endpoints:
  - `GET /market/ticker?instId=BTC-USDT`
  - `GET /market/candles?instId=BTC-USDT&bar=1H&limit=300`
  - `GET /market/tickers?instType=SPOT`
- Response envelope: `{ "code": "0", "data": [...] }` — `code` is a string.
- No API key required for public market data.
- Rate limits: OKX public endpoints have per-IP limits; adapter throttles.

### Usage terms (observed)

- OKX provides public market data; the adapter documents its own limits.
- Status: acceptable display/analysis source; resale requires re-verification.

---

## 5. Blocked/restricted providers (documented for future buyers)

### Binance

- **From this dev environment:** geo-blocked (HTTP 200 with
  `"Service unavailable from a restricted location"`).
- **Terms (observed):** Binance's Terms around market data have been cited as
  prohibiting without written consent: (a) trading services using Binance quotes;
  (b) data-feeding/streaming services using Binance market data; (c) any
  website/app that charges or profits (including ads) from market data obtained
  from Binance. This makes Binance **unsuitable as the default data source for a
  resale SaaS** without written consent.
- **Action:** Binance adapter code may exist behind the provider abstraction but
  is **disabled by default** with a documented warning. It is never used as the
  default analysis source.

### Bybit

- **From this dev environment:** HTTP 403 geo-blocked.
- **Terms:** Bybit's API docs describe rate limits; the Terms of Service apply to
  data use. Not selected as default for the same commercial-redistribution
  reasons as Binance (to be verified by buyer).

---

## 6. News sources

### Selected (default)

| Source | URL | Verified 2026-10-17 | Notes |
|---|---|---|---|
| CoinTelegraph RSS | `https://cointelegraph.com/rss` | ✅ 200 valid RSS 2.0 | Frequent crypto news, real timestamps, URLs |
| CoinDesk RSS | `https://www.coindesk.com/arc/outboundfeeds/rss/` | ⚠️ 308 redirect | Adapter follows redirects |

### Candidate sources (not selected for default, documented)

- CryptoPanic API: free tier exists but requires API key; noted for future.
- Coingecko trending: used only for watchlist inspiration (display values).

### News terms

- RSS feeds enable reading public article metadata (title, link, timestamp,
  description). Redistribution of full article text is not implied.
- **TrendCipher stores only the metadata the feed provides** (title, URL,
  published time, excerpt) plus internal classification fields, and links out to
  the original publisher. Full-text republication is not performed, minimizing
  copyright exposure.
- Publication time vs retrieval time are stored separately.

---

## 7. Price-reference source: CoinGecko

- `GET /api/v3/simple/price?ids=bitcoin&vs_currencies=usd` — free public demo.
- Used for display-only reference prices and watchlist convenience; not an
  authoritative analysis source.
- Free tier is rate-limited; adapter degrades gracefully.

---

## 8. Charting library

- **TradingView Lightweight Charts** — Apache-2.0, open source. GitHub:
  `https://github.com/tradingview/lightweight-charts`. Verified via TradingView's
  own page ("Lightweight Charts™ are open-source under the Apache 2.0 license").
- Attribution is required by the Apache-2.0 license; the web UI includes the
  attribution logo and a NOTICE/licenses reference.

---

## 9. Push notifications

- **Expo Notifications / Expo Push Service** — free for development; SDK 53+
  requires a development build (Expo Go no longer supports push on Android).
  Verified: `https://docs.expo.dev/versions/latest/sdk/notifications`.
- Real iOS push requires an Apple Developer account; we will not buy one.
- The backend abstracts delivery via `push_provider`; default dev-mode provider
  is `log` (LogOnly) with Expo configured as the device-facing provider.

---

## 10. Known limitations (honest inventory)

| Limitation | Impact | Mitigation |
|---|---|---|
| Binance/Bybit geo-block | Defaults must use Kraken/OKX | Adapter abstraction; documented |
| Kraken OHLC returns ~720 candles per request without paging | Backfill requires paging | Adapter paginates with `since` |
| CoinGecko free tier rate-limited | Display-only prices may lag | Non-critical; mark stale |
| No historical news archive via RSS | No back-history for news scenarios | Scenarios only use news available at runtime; documented |
| CoinDesk redirect | Needs redirect-following | Adapter uses `httpx` follow_redirects |
| Real push requires device + platform accounts | Cannot verify delivery here | LogOnly default; full docs for buyer |

---

## 11. Dependency license inventory (pointer)

Full inventory output is generated by CI/license tooling into
`docs/licenses/`. Key licenses at baseline:

| Dependency | License |
|---|---|
| Python / FastAPI / Uvicorn / SQLAlchemy / Pydantic | MIT / BSD (per package) |
| pytest / httpx / argon2-cffi | MIT / Apache-2.0 / CC0-1.0 (per package) |
| React / Vite / TypeScript | MIT |
| TradingView lightweight-charts | Apache-2.0 |
| Expo / React Native (sdk) | MIT |
| SQLite | Public domain |

The CI workflow runs a license check (pip-licenses + npm) and publishes the
generated inventory.