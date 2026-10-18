import { useEffect, useState } from 'react'
import {
  api,
  getToken,
  type BacktestResult,
  type ScenarioDetail,
  type TickerEntry,
} from '../lib/api'

const INTERVALS = ['1h', '4h', '1d'] as const

function fmtPrice(n: number | null | undefined) {
  if (n === null || n === undefined || Number.isNaN(n)) return '—'
  return new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 }).format(n)
}

export function Scanner() {
  const authed = Boolean(getToken())
  const [tickers, setTickers] = useState<TickerEntry[]>([])
  const [scenarios, setScenarios] = useState<ScenarioDetail[]>([])
  const [symbol, setSymbol] = useState('BTC/USD')
  const [interval, setInterval] = useState<(typeof INTERVALS)[number]>('1h')
  const [backtest, setBacktest] = useState<BacktestResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!authed) return
    Promise.all([api.getTickers(), api.getScenarios(undefined, 60)])
      .then(([t, s]) => {
        setTickers(t.tickers)
        setScenarios(s.scenarios)
      })
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load scanner'))
  }, [authed])

  useEffect(() => {
    if (!authed || !symbol) return
    api
      .runBacktest(symbol, interval, 400, 24)
      .then(setBacktest)
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to run backtest'))
  }, [authed, symbol, interval])

  if (!authed) {
    return (
      <section className="placeholder">
        <h2>You are not signed in</h2>
        <p>Sign in to use the signal scanner.</p>
      </section>
    )
  }

  const latestBySymbol = new Map<string, ScenarioDetail>()
  for (const s of scenarios) {
    if (!latestBySymbol.has(s.symbol)) latestBySymbol.set(s.symbol, s)
  }

  const bt = backtest?.stats

  return (
    <section className="dashboard">
      <div className="dashboard-header">
        <h2>Signal scanner</h2>
        {error && <div className="alert alert-error">{error}</div>}
      </div>

      <div className="card">
        <div className="card-toolbar">
          <h3>Markets &amp; scenarios</h3>
        </div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Price</th>
              <th>24h Δ</th>
              <th>Last scenario</th>
              <th>Alignment</th>
            </tr>
          </thead>
          <tbody>
            {tickers.map((t) => {
              const sc = latestBySymbol.get(t.symbol)
              return (
                <tr key={t.symbol}>
                  <td>
                    <button className="linklike" onClick={() => setSymbol(t.symbol)}>
                      {t.symbol}
                    </button>
                  </td>
                  <td>{fmtPrice(t.last_price)}</td>
                  <td>
                    {t.change_24h_pct != null ? (
                      <span style={{ color: t.change_24h_pct >= 0 ? 'var(--c-bull)' : 'var(--c-bear)' }}>
                        {t.change_24h_pct >= 0 ? '+' : ''}
                        {t.change_24h_pct.toFixed(2)}%
                      </span>
                    ) : (
                      '—'
                    )}
                  </td>
                  <td>
                    {sc ? (
                      <span className={`badge badge-${sc.direction.toLowerCase()}`}>{sc.direction}</span>
                    ) : (
                      <span className="muted">—</span>
                    )}
                  </td>
                  <td>
                    {sc?.alignment_score != null ? `${(sc.alignment_score * 100).toFixed(0)}%` : '—'}
                  </td>
                </tr>
              )
            })}
            {tickers.length === 0 && (
              <tr>
                <td colSpan={5} className="muted">
                  No tickers ingested yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="card">
        <div className="card-toolbar">
          <h3>Walk-forward backtest — {symbol}</h3>
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

        {bt ? (
          <div className="stat-grid">
            <div className="stat">
              <strong>{bt.trades}</strong>
              <span>Trades</span>
            </div>
            <div className="stat">
              <strong>{bt.winrate_pct.toFixed(1)}%</strong>
              <span>Win rate</span>
            </div>
            <div className="stat">
              <strong
                style={{ color: bt.total_pnl_pct >= 0 ? 'var(--c-bull)' : 'var(--c-bear)' }}
              >
                {bt.total_pnl_pct >= 0 ? '+' : ''}
                {bt.total_pnl_pct.toFixed(2)}%
              </strong>
              <span>Total PnL</span>
            </div>
            <div className="stat">
              <strong>{bt.hold_bars}</strong>
              <span>Hold bars</span>
            </div>
          </div>
        ) : (
          <p className="muted">Running backtest…</p>
        )}
      </div>
    </section>
  )
}