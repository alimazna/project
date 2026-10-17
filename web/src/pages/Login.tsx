import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, setToken } from '../lib/api'

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
    <div className="auth-page">
      <form className="auth-card" onSubmit={submit}>
        <h2>Sign in</h2>
        {error && <div className="alert alert-error">{error}</div>}
        <label>
          Email
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </label>
        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </label>
        <button className="btn btn-primary" type="submit" disabled={busy}>
          {busy ? 'Signing in…' : 'Sign in'}
        </button>
        <p className="muted">
          No account? <a href="/register">Register</a> — the first registered user
          becomes the administrator.
        </p>
      </form>
    </div>
  )
}