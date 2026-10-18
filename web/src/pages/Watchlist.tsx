import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, getToken, type TickerEntry, type Watchlist } from '../lib/api'

const ALL_SYMBOLS = [
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
  'ATOM/USD',
  'ETC/USD',
  'XTZ/USD',
  'ALGO/USD',
  'FIL/USD',
  'OP/USD',
  'ARB/USD',
  'APT/USD',
  'SUI/USD',
]

export function WatchlistPage() {
  const authed = Boolean(getToken())
  const [rows, setRows] = useState<Watchlist[]>([])
  const [tickers, setTickers] = useState<TickerEntry[]>([])
  const [name, setName] = useState('Default')
  const [picked, setPicked] = useState<string[]>(['BTC/USD', 'ETH/USD'])
  const [error, setError] = useState<string | null>(null)

  const load = () => {
    Promise.all([api.getWatchlists(), api.getTickers()])
      .then(([w, t]) => {
        setRows(w.watchlists)
        setTickers(t.tickers)
      })
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load watchlists'))
  }

  useEffect(() => {
    if (authed) load()
  }, [authed])

  const create = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    try {
      await api.createWatchlist(name, picked)
      setName('Default')
      setPicked([])
      load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not create watchlist')
    }
  }

  const remove = async (id: number) => {
    setError(null)
    try {
      await api.deleteWatchlist(id)
      load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not delete watchlist')
    }
  }

  const toggleSymbol = (sym: string) =>
    setPicked((prev) => (prev.includes(sym) ? prev.filter((s) => s !== sym) : [...prev, sym]))

  if (!authed) {
    return (
      <section className="placeholder">
        <h2>You are not signed in</h2>
        <p>Sign in to manage your watchlist.</p>
      </section>
    )
  }

  const tickerMap = new Map(tickers.map((t) => [t.symbol, t.last_price]))

  return (
    <section className="dashboard">
      <div className="dashboard-header">
        <h2>Watchlist</h2>
        {error && <div className="alert alert-error">{error}</div>}
      </div>

      <form className="card" onSubmit={create}>
        <h3>Create a watchlist</h3>
        <label>
          Name
          <input value={name} onChange={(e) => setName(e.target.value)} required />
        </label>
        <div className="picker">
          {ALL_SYMBOLS.map((sym) => (
            <button
              key={sym}
              type="button"
              className={`ticker-chip ${picked.includes(sym) ? 'ticker-chip-active' : ''}`}
              onClick={() => toggleSymbol(sym)}
            >
              {sym}
            </button>
          ))}
        </div>
        <button className="btn btn-primary" type="submit" disabled={picked.length === 0}>
          Create ({picked.length})
        </button>
      </form>

      {rows.length === 0 && (
        <p className="muted">No watchlists yet — create one above.</p>
      )}

      {rows.map((w) => (
        <div className="card" key={w.id}>
          <div className="card-toolbar">
            <h3>{w.name}</h3>
            <button className="btn btn-small btn-outline" onClick={() => remove(w.id)}>
              Delete
            </button>
          </div>
          <div className="ticker-strip">
            {w.symbols.map((sym) => (
              <Link key={sym} className="ticker-chip" to={`/asset/${encodeURIComponent(sym)}`}>
                <span className="ticker-symbol">{sym}</span>
                <span className="ticker-price">
                  {tickerMap.get(sym) != null ? `$${tickerMap.get(sym)?.toFixed(2)}` : '—'}
                </span>
              </Link>
            ))}
            {w.symbols.length === 0 && <span className="muted">Empty</span>}
          </div>
        </div>
      ))}
    </section>
  )
}