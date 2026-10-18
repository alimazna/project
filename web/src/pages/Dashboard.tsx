import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  api,
  getToken,
  type CandleEntry,
  type HealthResult,
  type NewsEntry,
  type ScenarioDetail,
  type TickerEntry,
} from '../lib/api'
import { CandleChart, type ChartLevel } from '../components/CandleChart'

const INTERVALS = ['1h', '4h', '1d'] as const

function fmtPrice(n: number | null | undefined) {
  if (n === null || n === undefined || Number.isNaN(n)) return '—'
  return new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 }).format(n)
}

function fmtTime(iso: string | null | undefined) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString()
}

function fmtPct(n: number | null | undefined) {
  if (n === null || n === undefined || Number.isNaN(n)) return '—'
  return `${(n * 100).toFixed(0)}%`
}

function directionLabel(d: string) {
  if (d === 'BULLISH') return '▲ Bullish'
  if (d === 'BEARISH') return '▼ Bearish'
  return '◆ Neutral'
}

export function Dashboard() {
  const authed = Boolean(getToken())
  const [health, setHealth] = useState<HealthResult | null>(null)
  const [tickers, setTickers] = useState<TickerEntry[]>([])
  const [news, setNews] = useState<NewsEntry[]>([])
  const [allNews, setAllNews] = useState<NewsEntry[]>([])
  const [newsSource, setNewsSource] = useState('')
  const [error, setError] = useState<string | null>(null)

  const [selected, setSelected] = useState('BTC/USD')
  const [interval, setInterval] = useState<(typeof INTERVALS)[number]>('1h')
  const [candles, setCandles] = useState<CandleEntry[]>([])
  const [candleLoading, setCandleLoading] = useState(false)

  const [scenario, setScenario] = useState<ScenarioDetail | null>(null)
  const [scenarioLoading, setScenarioLoading] = useState(false)

  useEffect(() => {
    Promise.all([api.getHealth(), api.getSymbols(), api.getTickers(), api.getNews(12)])
      .then(([h, s, t, n]) => {
        setHealth(h)
        setTickers(t.tickers)
        setAllNews(n.articles)
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
    if (!newsSource) {
      setNews(allNews)
      return
    }
    api
      .getNews(12, newsSource)
      .then((r) => setNews(r.articles))
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to filter news'))
  }, [newsSource, allNews])

  useEffect(() => {
    if (!selected) return
    setCandleLoading(true)
    api
      .getCandles(selected, interval, 100)
      .then((r) => setCandles(r.candles))
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load candles'))
      .finally(() => setCandleLoading(false))
  }, [selected, interval])

  const refreshScenario = useCallback(() => {
    if (!selected) return
    setScenarioLoading(true)
    api
      .runAnalysis(selected, interval, 120, true)
      .then((r) => setScenario(r.scenario))
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to compute scenario'))
      .finally(() => setScenarioLoading(false))
  }, [selected, interval])

  useEffect(() => {
    refreshScenario()
  }, [refreshScenario])

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

  const assetLink = `/asset/${encodeURIComponent(selected)}`

  const chartLevels: ChartLevel[] = []
  if (scenario && scenario.direction !== 'NEUTRAL') {
    if (scenario.entry_low != null)
      chartLevels.push({ price: scenario.entry_low, label: 'Entry', color: '#4f8cff' })
    if (scenario.entry_high != null && scenario.entry_high !== scenario.entry_low)
      chartLevels.push({ price: scenario.entry_high, label: 'Entry', color: '#4f8cff' })
    if (scenario.stop_loss != null)
      chartLevels.push({ price: scenario.stop_loss, label: 'Stop', color: '#ef4444' })
    for (const tp of scenario.take_profits ?? [])
      chartLevels.push({ price: tp, label: 'TP', color: '#22c55e' })
  }

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
        {/* Scenario card */}
        <div className="card">
          <div className="card-toolbar">
            <h3>Scenario — explainable</h3>
            <button
              className="btn btn-small"
              onClick={refreshScenario}
              disabled={scenarioLoading}
            >
              {scenarioLoading ? '…' : 'Re-run'}
            </button>
          </div>

          {!scenario && !scenarioLoading && (
            <p className="muted">No scenario computed yet.</p>
          )}
          {scenarioLoading && <p className="muted">Running decision matrix…</p>}

          {scenario && !scenarioLoading && (
            <>
              <div className="scenario-head">
                <span className={`badge badge-${scenario.direction.toLowerCase()}`}>
                  {directionLabel(scenario.direction)}
                </span>
                <span className="muted small">
                  {scenario.symbol} · {scenario.timeframe} · {scenario.rule_version}
                </span>
              </div>

              <div className="price-row">
                <span className="price-big">{fmtPrice(scenario.last_close)}</span>
                <span className="muted">alignment {fmtPct(scenario.alignment_score)}</span>
              </div>

              {scenario.direction !== 'NEUTRAL' && (
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Entry</th>
                      <th>Stop</th>
                      <th>Targets</th>
                      <th>R/R</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td>
                        {fmtPrice(scenario.entry_low)}
                        {scenario.entry_high && scenario.entry_high !== scenario.entry_low
                          ? `–${fmtPrice(scenario.entry_high)}`
                          : ''}
                      </td>
                      <td>{fmtPrice(scenario.stop_loss)}</td>
                      <td>{scenario.take_profits.map(fmtPrice).join(' / ') || '—'}</td>
                      <td>{scenario.risk_reward ?? '—'}</td>
                    </tr>
                  </tbody>
                </table>
              )}

              <div className="scenario-drivers">
                <h4>Why?</h4>
                <ul>
                  {scenario.decisions.map((d) => (
                    <li key={d.signal}>
                      <span className={`badge badge-vote badge-vote-${Math.sign(d.vote)}`}>
                        {d.vote > 0 ? '+' : d.vote < 0 ? '−' : '·'}
                      </span>
                      <span className="muted small">{d.signal.replace(/_/g, ' ')}</span>
                      <span className="small">{d.reason}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </>
          )}
        </div>

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

          {!candleLoading && candles.length > 0 && (
            <>
              <div className="price-row">
                <span className="price-big">{fmtPrice(lastCandle?.close)}</span>
                <span className="muted small">
                  <Link to={assetLink}>Open asset detail →</Link> · {selected} · {interval} ·{' '}
                  {candles.length} candles
                </span>
              </div>
              <CandleChart candles={candles} levels={chartLevels} height={320} />
              {scenario?.direction !== 'NEUTRAL' && (
                <p className="muted small">
                  Entry {fmtPrice(scenario?.entry_low)}
                  {scenario?.entry_high && scenario.entry_high !== scenario.entry_low
                    ? `–${fmtPrice(scenario.entry_high)}`
                    : ''}{' '}
                  · Stop {fmtPrice(scenario?.stop_loss)} · Targets{' '}
                  {scenario?.take_profits.map(fmtPrice).join(' / ') || '—'} — plotted as
                  dashed lines.
                </p>
              )}
            </>
          )}
        </div>

        {/* News card */}
        <div className="card">
          <div className="news-header">
            <h3>Recent news</h3>
            {allNews.length > 1 && (
              <select
                className="news-filter"
                value={newsSource}
                onChange={(e) => setNewsSource(e.target.value)}
                aria-label="Filter news by source"
              >
                <option value="">All sources</option>
                {[...new Set(allNews.map((a) => a.source))].map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            )}
          </div>
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