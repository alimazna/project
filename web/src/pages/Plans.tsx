import { useEffect, useState } from 'react'
import { api, getToken } from '../lib/api'

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
  const [current, setCurrent] = useState<string | null>(null)
  const [busy, setBusy] = useState<string | null>(null)
  const authed = Boolean(getToken())

  useEffect(() => {
    api
      .get<{ items: Plan[] }>('/plans')
      .then((d) => setPlans(d.items))
      .catch((e) => setError(e instanceof Error ? e.message : 'Could not load plans'))
    if (authed) {
      api
        .get<{ plan: { code: string } }>('/me/subscription')
        .then((m) => setCurrent(m.plan.code))
        .catch(() => {})
    }
  }, [authed])

  const choose = async (code: string) => {
    setBusy(code)
    setError(null)
    try {
      const res = await api.put<{ plan: { code: string } }>('/me/subscription', {
        plan_code: code,
      })
      setCurrent(res.plan.code)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not subscribe')
    } finally {
      setBusy(null)
    }
  }

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
            {authed ? (
              <button
                className={`btn ${current === p.code ? 'btn-primary' : 'btn-outline'}`}
                onClick={() => choose(p.code)}
                disabled={busy !== null || current === p.code}
              >
                {current === p.code
                  ? 'Your plan'
                  : busy === p.code
                    ? 'Applying…'
                    : p.billing_interval === 'none'
                      ? 'Start free'
                      : 'Upgrade'}
              </button>
            ) : (
              <button className="btn btn-outline" onClick={() => (window.location.href = '/login')}>
                Sign in to choose
              </button>
            )}
          </div>
        ))}
      </div>
    </section>
  )
}