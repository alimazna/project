import { useEffect, useState } from 'react'
import {
  api,
  getToken,
  type AlertDeliveryEntry,
  type UserAlert,
} from '../lib/api'

const KINDS = [
  { id: 'price_above', label: 'Price above' },
  { id: 'price_below', label: 'Price below' },
  { id: 'scenario_bullish', label: 'Bullish scenario' },
  { id: 'scenario_bearish', label: 'Bearish scenario' },
  { id: 'news_relevance', label: 'Relevant news' },
]

const SYMBOLS = [
  'BTC/USD',
  'ETH/USD',
  'SOL/USD',
  'XRP/USD',
  'ADA/USD',
  'DOGE/USD',
  'LINK/USD',
  'DOT/USD',
  'LTC/USD',
  'AVAX/USD',
  'POL/USD',
  'UNI/USD',
  'OP/USD',
  'ARB/USD',
  'APT/USD',
  'SUI/USD',
]

function fmtTime(iso: string | null | undefined) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString()
}

function kindLabel(kind: string) {
  return KINDS.find((k) => k.id === kind)?.label ?? kind
}

export function Alerts() {
  const authed = Boolean(getToken())
  const [rows, setRows] = useState<UserAlert[]>([])
  const [deliveries, setDeliveries] = useState<AlertDeliveryEntry[]>([])
  const [symbol, setSymbol] = useState('BTC/USD')
  const [kind, setKind] = useState('price_above')
  const [value, setValue] = useState('')
  const [error, setError] = useState<string | null>(null)

  const load = () => {
    Promise.all([api.getAlerts(), api.getAlertDeliveries(15)])
      .then(([a, d]) => {
        setRows(a.alerts)
        setDeliveries(d.deliveries)
      })
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load alerts'))
  }

  useEffect(() => {
    if (authed) load()
  }, [authed])

  const create = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    const needsValue = kind === 'price_above' || kind === 'price_below'
    const numValue = needsValue ? Number(value) : undefined
    if (needsValue && (!value || Number.isNaN(numValue))) {
      setError('Price alerts need a numeric threshold.')
      return
    }
    try {
      await api.createAlert(symbol, kind, numValue)
      setValue('')
      load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not create alert')
    }
  }

  const toggle = async (alert: UserAlert) => {
    setError(null)
    try {
      await api.updateAlert(alert.id, { is_active: !alert.is_active })
      load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not update alert')
    }
  }

  const remove = async (id: number) => {
    setError(null)
    try {
      await api.deleteAlert(id)
      load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not delete alert')
    }
  }

  if (!authed) {
    return (
      <section className="placeholder">
        <h2>You are not signed in</h2>
        <p>Sign in to manage price, scenario and news alerts.</p>
      </section>
    )
  }

  return (
    <section className="dashboard">
      <div className="dashboard-header">
        <h2>Alerts</h2>
        {error && <div className="alert alert-error">{error}</div>}
      </div>

      <form className="card" onSubmit={create}>
        <h3>Create an alert</h3>
        <div className="alert-form">
          <label>
            Symbol
            <select value={symbol} onChange={(e) => setSymbol(e.target.value)}>
              {SYMBOLS.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </label>
          <label>
            Condition
            <select value={kind} onChange={(e) => setKind(e.target.value)}>
              {KINDS.map((k) => (
                <option key={k.id} value={k.id}>
                  {k.label}
                </option>
              ))}
            </select>
          </label>
          {(kind === 'price_above' || kind === 'price_below') && (
            <label>
              Threshold (USD)
              <input
                type="number"
                step="any"
                value={value}
                onChange={(e) => setValue(e.target.value)}
                placeholder="e.g. 70000"
              />
            </label>
          )}
        </div>
        <button className="btn btn-primary" type="submit">
          Create
        </button>
      </form>

      <div className="card">
        <h3>Your alerts</h3>
        {rows.length === 0 && <p className="muted">No alerts yet — create one above.</p>}
        <table className="data-table">
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Condition</th>
              <th>Last fired</th>
              <th>State</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((a) => (
              <tr key={a.id}>
                <td>{a.symbol}</td>
                <td>
                  {kindLabel(a.kind)}
                  {a.value != null ? ` @ ${a.value}` : ''}
                </td>
                <td className="muted small">{fmtTime(a.last_fired_at)}</td>
                <td>
                  <span className={`badge ${a.is_active ? 'badge-ok' : 'badge-unknown'}`}>
                    {a.is_active ? 'Active' : 'Paused'}
                  </span>
                </td>
                <td>
                  <button className="btn btn-small" onClick={() => toggle(a)}>
                    {a.is_active ? 'Pause' : 'Resume'}
                  </button>{' '}
                  <button className="btn btn-small btn-outline" onClick={() => remove(a.id)}>
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card">
        <h3>Delivery log</h3>
        {deliveries.length === 0 && <p className="muted">No alert deliveries yet.</p>}
        <table className="data-table">
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Channel</th>
              <th>Status</th>
              <th>When</th>
            </tr>
          </thead>
          <tbody>
            {deliveries.map((d) => (
              <tr key={d.id}>
                <td>{d.symbol ?? `alert #${d.alert_id}`}</td>
                <td>{d.channel}</td>
                <td>
                  <span className={`badge ${d.status === 'delivered' ? 'badge-ok' : 'badge-unknown'}`}>
                    {d.status}
                  </span>
                </td>
                <td className="muted small">{fmtTime(d.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}