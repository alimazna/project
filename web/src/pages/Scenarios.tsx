import { useEffect, useState } from 'react'
import { api, getToken, type ScenarioDetail } from '../lib/api'

function fmtPrice(n: number | null | undefined) {
  if (n === null || n === undefined || Number.isNaN(n)) return '—'
  return new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 }).format(n)
}

function directionLabel(d: string) {
  if (d === 'BULLISH') return '▲ Bullish'
  if (d === 'BEARISH') return '▼ Bearish'
  return '◆ Neutral'
}

export function Scenarios() {
  const authed = Boolean(getToken())
  const [symbol, setSymbol] = useState('')
  const [rows, setRows] = useState<ScenarioDetail[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .getScenarios(symbol || undefined, 30)
      .then((r) => setRows(r.scenarios))
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load scenarios'))
  }, [symbol])

  if (!authed) {
    return (
      <section className="placeholder">
        <h2>You are not signed in</h2>
        <p>Sign in to review computed scenarios.</p>
      </section>
    )
  }

  return (
    <section className="dashboard">
      <div className="dashboard-header">
        <h2>Scenario history</h2>
        <input
          className="input"
          placeholder="Filter by symbol (e.g. BTC/USD)"
          value={symbol}
          onChange={(e) => setSymbol(e.target.value)}
        />
        {error && <div className="alert alert-error">{error}</div>}
      </div>

      {rows.length === 0 && <p className="muted">No scenarios computed yet — run analysis on the dashboard.</p>}

      <div className="card">
        <table className="data-table">
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Direction</th>
              <th>TF</th>
              <th>Alignment</th>
              <th>Entry</th>
              <th>Stop</th>
              <th>R/R</th>
              <th>Rule</th>
              <th>When</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id ?? r.created_at}>
                <td>{r.symbol}</td>
                <td>
                  <span className={`badge badge-${r.direction.toLowerCase()}`}>
                    {directionLabel(r.direction)}
                  </span>
                </td>
                <td>{r.timeframe}</td>
                <td>{r.alignment_score != null ? `${(r.alignment_score * 100).toFixed(0)}%` : '—'}</td>
                <td>
                  {fmtPrice(r.entry_low)}
                  {r.entry_high && r.entry_high !== r.entry_low ? `-${fmtPrice(r.entry_high)}` : ''}
                </td>
                <td>{fmtPrice(r.stop_loss)}</td>
                <td>{r.risk_reward ?? '—'}</td>
                <td className="muted small">{r.rule_version}</td>
                <td className="muted small">{r.created_at ? new Date(r.created_at).toLocaleString() : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}