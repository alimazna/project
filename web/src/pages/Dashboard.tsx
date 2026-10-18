import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  api,
  getToken,
  type CandleEntry,
  type HealthResult,
  type NewsEntry,
  type TickerEntry,
} from '../lib/api'

const INTERVALS = ['1h', '4h', '1d'] as const

function fmtPrice(n: number | null | undefined) {
  if (n === null || n === undefined || Number.isNaN(n)) return '—'
  return new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 }).format(n)
}

function fmtTime(iso: string | null | undefined) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString()
}

function sparklineColor(candles: CandleEntry[]): string {
  if (candles.length < 2) return 'var(--muted)'
  return candles[candles.length - 1].close >= candles[0].open ? '#10b981' : '#ef4444'
}

function Sparkline({ candles }: { candles: CandleEntry[] }) {
  if (candles.length < 2) return null
  const max = Math.max(...candles.map((c) => c.high))
  const min = Math.min(...candles.map((c) => c.low))
  const range = max - min || 1
  const width = 120
  const height = 36
  const pts = candles
    .map((c, i) => {
      const x = (i / (candles.length - 1)) * width
      const y = height - ((c.close - min) / range) * (height - 4) - 2
      return `${x.toFixed(1)},${y.toFixed(1)}`
    })
    .join(' ')
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} aria-hidden="true">
      <polyline fill="none" stroke={sparklineColor(candles)} strokeWidth="1.5" points={pts} />
    </svg>
  )
}

export function Dashboard() {
  const authed = Boolean(getToken())
  const [health, setHealth] = useState<HealthResult | null>(null)
  const [tickers, setTickers] = useState<TickerEntry[]>([])
  const [news, setNews] = useState<NewsEntry[]>([])
  const [error, setError] = useState<string | null>(null)

  const [selected, setSelected] = useState('BTC/USD')
  const [interval, setInterval] = useState<(typeof INTERVALS)[number]>('1h')
  const [candles, setCandles] = useState<CandleEntry[]>([])
  const [candleLoading, setCandleLoading] = useState(false)

  useEffect(() => {
    Promise.all([api.getHealth(), api.getSymbols(), api.getTickers(), api.getNews(12)])
      .then(([h, s, t, n]) => {
        setHealth(h)
        setTickers(t.tickers)
        setNews(n.articles)
        if (s.symbols.length > 0) {
          setSelected((prev) =>
            s.symbols.some((x) => x.symbol === prev) ? prev : s.symbols[0].symbol,
          )
        }
      })
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load market data'))
  }, [])

  useEffect(() => {
    if (!selected) return
    setCandleLoading(true)
    api
      .getCandles(selected, interval, 100)
      .then((r) => setCandles(r.candles))
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load candles'))
      .finally(() => setCandleLoading(false))
  }, [selected, interval])

  if (!authed) {
    return (
      <section className="placeholder">
        <h2>You are not signed in</h2>
        <p>
          The analytical dashboard requires an account. The first registered user
          becomes the administrator.
        </p>
        <Link className="btn btn-primary" to="/register">
          Create account
        </Link>
      </section>
    )
  }

  const selectedTicker = tickers.find((t) => t.symbol === selected)
  const lastCandle = candles[candles.length - 1]

  return (
    <section className="dashboard">
      <div className="dashboard-header">
        <h2>Market Overview</h2>
        {selectedTicker && (
          <span className="header-price">
            {selectedTicker.symbol} ≈ {fmtPrice(selectedTicker.last_price)}
            {selectedTicker.high_24h ? ` · 24h High ${fmtPrice(selectedTicker.high_24h)}` : ''}
          </span>
        )}
        {error && <div className="alert alert-error">{error}</div>}
      </div>

      {/* Ticker strip */}
      <div className="ticker-strip">
        {tickers.map((t) => (
          <button
            key={t.symbol}
            className={`ticker-chip ${t.symbol === selected ? 'ticker-chip-active' : ''}`}
            onClick={() => setSelected(t.symbol)}
          >
            <span className="ticker-symbol">{t.symbol}</span>
            <span className="ticker-price">{fmtPrice(t.last_price)}</span>
          </button>
        ))}
      </div>

      <div className="grid-2">
        {/* Chart card */}
        <div className="card">
          <div className="card-toolbar">
            <h3>{selected} — candles</h3>
            <div className="segmented">
              {INTERVALS.map((iv) => (
                <button
                  key={iv}
                  className={iv === interval ? 'segmented-active' : ''}
                  onClick={() => setInterval(iv)}
                >
                  {iv}
                </button>
              ))}
            </div>
          </div>

          {candleLoading && <p className="muted">Loading candles…</p>}

          {!candleLoading && lastCandle && (
            <>
              <div className="price-row">
                <span className="price-big">{fmtPrice(lastCandle.close)}</span>
                <Sparkline candles={candles.slice(-40)} />
              </div>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Open</th>
                    <th>High</th>
                    <th>Low</th>
                    <th>Close</th>
                    <th>Volume</th>
                  </tr>
                </thead>
                <tbody>
                  {candles
                    .slice(-10)
                    .map((c) => (
                      <tr key={c.open_time}>
                        <td>{fmtPrice(c.open)}</td>
                        <td>{fmtPrice(c.high)}</td>
                        <td>{fmtPrice(c.low)}</td>
                        <td>{fmtPrice(c.close)}</td>
                        <td>{fmtPrice(c.volume)}</td>
                      </tr>
                    ))}
                </tbody>
              </table>
              <p className="muted small">
                Last 10 candles · {selected} · {interval}
              </p>
            </>
          )}
        </div>

        {/* News card */}
        <div className="card">
          <h3>Recent news</h3>
          {news.length === 0 && <p className="muted">No articles ingested yet.</p>}
          <ul className="news-list">
            {news.map((a) => (
              <li key={a.id}>
                <span className="news-source">{a.source}</span>
                <a href={a.url} target="_blank" rel="noreferrer">
                  {a.title}
                </a>
                <span className="news-time">{fmtTime(a.published_at)}</span>
                {a.assets && a.assets !== '[]' && <span className="news-assets">{a.assets}</span>}
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Provider health */}
      <div className="card">
        <h3>Data pipeline health</h3>
        {(health?.providers ?? []).length === 0 && (
          <p className="muted">
            No ingestion runs recorded yet. Start the worker:
            <code> python -m app.workers.ingestion</code>
          </p>
        )}
        <ul className="health-list">
          {(health?.providers ?? []).map((p) => (
            <li key={p.provider}>
              <span className={`badge badge-${p.status}`}>{p.status}</span>
              <strong>{p.provider}</strong>
              <span className="muted small">{fmtTime(p.last_success_at)}</span>
              {p.last_error && <span className="alert alert-error">{p.last_error}</span>}
            </li>
          ))}
        </ul>
      </div>
    </section>
  )
}