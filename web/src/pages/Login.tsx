import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, setToken } from '../lib/api'
import { appName } from '../lib/config'

export function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const navigate = useNavigate()

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const res = await api.post<{ access_token: string; refresh_token: string }>('/auth/login', {
        email,
        password,
      })
      setToken(res.access_token)
      // refresh token: stored for session continuity (not exposed to UI)
      window.sessionStorage.setItem('tc_refresh', res.refresh_token)
      navigate('/dashboard')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="auth-page auth-page-split">
      <div className="auth-intro">
        <h2>
          Unlock Predictive <span className="emph">Insights</span> with AI-Powered
          Statistical Analytics
        </h2>
        <p className="muted">{appName()}: an AI-powered statistical analytics platform.</p>
        <div className="chip-row" style={{ justifyContent: 'flex-start' }}>
          <span className="feature-chip">Real-time Processing</span>
          <span className="feature-chip blue">Advanced Forecasting</span>
          <span className="feature-chip green">Automated Insights</span>
        </div>
      </div>
      <form className="auth-card" onSubmit={submit}>
        <h2>Sign in</h2>
        {error && <div className="alert alert-error">{error}</div>}
        <label>
          Email
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            required
          />
        </label>
        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            required
          />
        </label>
        <button className="btn btn-primary" type="submit" disabled={busy}>
          {busy ? 'Signing in…' : 'Sign in'}
        </button>
        <p className="muted">
          Don't have an account? <a href="/register">Sign Up Free</a>
        </p>
      </form>
    </div>
  )
}