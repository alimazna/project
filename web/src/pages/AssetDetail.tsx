import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  api,
  getToken,
  type CandleEntry,
  type NewsEntry,
  type ScenarioDetail,
  type TickerEntry,
} from '../lib/api'
import { CandleChart, type ChartLevel } from '../components/CandleChart'

const INTERVALS = ['1h', '4h', '1d'] as const
const CANDLE_LIMIT = 300

function fmtPrice(n: number | null | undefined) {
  if (n === null || n === undefined || Number.isNaN(n)) return '—'
  return new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 }).format(n)
}

function fmtTime(iso: string | null | undefined) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString()
}

function directionLabel(d: string) {
  if (d === 'BULLISH') return '▲ Bullish'
  if (d === 'BEARISH') return '▼ Bearish'
  return '◆ Neutral'
}

function buildLevels(scenario: ScenarioDetail | null): ChartLevel[] {
  const out: ChartLevel[] = []
  if (!scenario || scenario.direction === 'NEUTRAL') return out
  if (scenario.entry_low != null)
    out.push({ price: scenario.entry_low, label: 'Entry', color: '#4f8cff' })
  if (scenario.entry_high != null && scenario.entry_high !== scenario.entry_low)
    out.push({ price: scenario.entry_high, label: 'Entry', color: '#4f8cff' })
  if (scenario.stop_loss != null)
    out.push({ price: scenario.stop_loss, label: 'Stop', color: '#ef4444' })
  for (const tp of scenario.take_profits ?? [])
    out.push({ price: tp, label: 'TP', color: '#22c55e' })
  return out
}

export function AssetDetail() {
  const { symbol = 'BTC/USD' } = useParams()
  const authed = Boolean(getToken())
  const [interval, setInterval] = useState<(typeof INTERVALS)[number]>('1h')
  const [candles, setCandles] = useState<CandleEntry[]>([])
  const [ticker, setTicker] = useState<TickerEntry | null>(null)
  const [news, setNews] = useState<NewsEntry[]>([])
  const [scenario, setScenario] = useState<ScenarioDetail | null>(null)
  const [history, setHistory] = useState<ScenarioDetail[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!symbol) return
    setLoading(true)
    Promise.all([
      api.getCandles(symbol, interval, CANDLE_LIMIT),
      api.getTickers().then((r) => r.tickers.find((t) => t.symbol === symbol) ?? null),
      api.getNews(20),
      api.runAnalysis(symbol, interval, 120, true),
      api.getScenarios(symbol, 10),
    ])
      .then(([c, t, n, s, h]) => {
        setCandles(c.candles)
        setTicker(t)
        setNews(n.articles.filter((a) => (a.assets || '[]').includes(symbol)))
        setScenario(s.scenario)
        setHistory(h.scenarios)
      })
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load asset'))
      .finally(() => setLoading(false))
  }, [symbol, interval])

  if (!authed) {
    return (
      <section className="placeholder">
        <h2>You are not signed in</h2>
        <p>Sign in to view asset analysis.</p>
        <Link className="btn btn-primary" to="/login">
          Sign in
        </Link>
      </section>
    )
  }

  return (
    <section className="dashboard">
      <div className="dashboard-header">
        <h2>{symbol}</h2>
        {ticker && (
          <span className="header-price">
            ≈ {fmtPrice(ticker.last_price)}
            {ticker.high_24h ? ` · 24h High ${fmtPrice(ticker.high_24h)}` : ''}
          </span>
        )}
        {error && <div className="alert alert-error">{error}</div>}
      </div>

      <div className="card">
        <div className="card-toolbar">
          <h3>Price chart</h3>
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
        {loading && <p className="muted">Loading…</p>}
        {!loading && candles.length > 0 && (
          <CandleChart candles={candles} levels={buildLevels(scenario)} height={400} />
        )}
        {!loading && candles.length === 0 && <p className="muted">No candles available.</p>}
      </div>

      <div className="card">
        <h3>Scenario — explainable</h3>
        {scenario ? (
          <>
            <div className="scenario-head">
              <span className={`badge badge-${scenario.direction.toLowerCase()}`}>
                {directionLabel(scenario.direction)}
              </span>
              <span className="muted small">
                {scenario.timeframe} · {scenario.rule_version} · alignment{' '}
                {scenario.alignment_score != null
                  ? `${(scenario.alignment_score * 100).toFixed(0)}%`
                  : '—'}
              </span>
            </div>
            <div className="price-row">
              <span className="price-big">{fmtPrice(scenario.last_close)}</span>
              {scenario.risk_reward ? (
                <span className="muted">R/R {scenario.risk_reward}</span>
              ) : null}
            </div>
            {scenario.direction !== 'NEUTRAL' && (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Entry</th>
                    <th>Stop</th>
                    <th>Targets</th>
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
        ) : (
          <p className="muted">No scenario computed yet.</p>
        )}
      </div>

      <div className="grid-2">
        <div className="card">
          <h3>Related news</h3>
          {news.length === 0 && <p className="muted">No related articles yet.</p>}
          <ul className="news-list">
            {news.map((a) => (
              <li key={a.id}>
                <span className="news-source">{a.source}</span>
                <a href={a.url} target="_blank" rel="noreferrer">
                  {a.title}
                </a>
                <span className="news-time">{fmtTime(a.published_at)}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="card">
          <h3>Scenario history</h3>
          {history.length === 0 && <p className="muted">No prior scenarios.</p>}
          <table className="data-table">
            <thead>
              <tr>
                <th>Direction</th>
                <th>Alignment</th>
                <th>R/R</th>
                <th>When</th>
              </tr>
            </thead>
            <tbody>
              {history.slice(0, 8).map((r) => (
                <tr key={r.id ?? r.created_at}>
                  <td>
                    <span className={`badge badge-${r.direction.toLowerCase()}`}>
                      {directionLabel(r.direction)}
                    </span>
                  </td>
                  <td>{r.alignment_score != null ? `${(r.alignment_score * 100).toFixed(0)}%` : '—'}</td>
                  <td>{r.risk_reward ?? '—'}</td>
                  <td className="muted small">{r.created_at ? new Date(r.created_at).toLocaleString() : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  )
}