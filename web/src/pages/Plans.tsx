import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../lib/api'

interface Plan {
  code: string
  name: string
  description: string | null
  display_price: string
  billing_interval: string
  currency: string
  features: string[]
  quotas: Record<string, number>
}

export function Plans() {
  const [plans, setPlans] = useState<Plan[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .get<{ items: Plan[] }>('/plans')
      .then((d) => setPlans(d.items))
      .catch((e) => setError(e instanceof Error ? e.message : 'Could not load plans'))
  }, [])

  return (
    <section className="plans-page">
      <h2>Pricing</h2>
      <p className="muted">
        Plans are managed by the operator and rendered live from the backend.
      </p>
      {error && <div className="alert alert-error">{error}</div>}
      <div className="plan-grid">
        {plans === null && <div className="muted">Loading plans…</div>}
        {plans?.map((p) => (
          <div className="card plan-card" key={p.code}>
            <h3>{p.name}</h3>
            <div className="plan-price">
              {p.display_price}
              {p.billing_interval !== 'none' && (
                <span className="muted"> / {p.billing_interval}</span>
              )}
            </div>
            <p>{p.description}</p>
            <ul>
              {(p.features ?? []).map((f) => (
                <li key={f}>{f}</li>
              ))}
            </ul>
            <Link className="btn btn-outline" to="/register">
              Get started
            </Link>
          </div>
        ))}
      </div>
    </section>
  )
}