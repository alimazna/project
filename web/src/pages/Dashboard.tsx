import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, getToken } from '../lib/api'

interface HealthResult {
  status: string
  providers: { provider: string; status: string }[]
}

export function Dashboard() {
  const [health, setHealth] = useState<HealthResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const authed = Boolean(getToken())

  useEffect(() => {
    api
      .get<HealthResult>('/health')
      .then(setHealth)
      .catch((e) => setError(e instanceof Error ? e.message : 'Health check failed'))
  }, [])

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

  return (
    <section className="dashboard">
      <h2>Overview</h2>
      {error && <div className="alert alert-error">{error}</div>}
      <div className="grid-2">
        <div className="card">
          <h3>System health</h3>
          <p>
            Backend: <strong>{health?.status ?? 'checking…'}</strong>
          </p>
          <ul>
            {(health?.providers ?? []).map((p) => (
              <li key={p.provider}>
                {p.provider}: {p.status}
              </li>
            ))}
          </ul>
        </div>
        <div className="card">
          <h3>Data pipeline</h3>
          <p>
            Market data and news ingestion will appear here once the ingestion
            workers are running. See the roadmap in the repository docs.
          </p>
        </div>
      </div>
    </section>
  )
}