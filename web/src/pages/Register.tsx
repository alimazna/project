import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, setToken } from '../lib/api'

export function Register() {
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
      const res = await api.post<{ access_token: string; refresh_token: string }>(
        '/auth/register',
        { email, password },
      )
      setToken(res.access_token)
      window.sessionStorage.setItem('tc_refresh', res.refresh_token)
      navigate('/dashboard')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="auth-page">
      <form className="auth-card" onSubmit={submit}>
        <h2>Create account</h2>
        {error && <div className="alert alert-error">{error}</div>}
        <label>
          Email
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </label>
        <label>
          Password (min 8 characters)
          <input
            type="password"
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </label>
        <button className="btn btn-primary" type="submit" disabled={busy}>
          {busy ? 'Creating…' : 'Create account'}
        </button>
        <p className="muted">
          Already registered? <a href="/login">Sign in</a>
        </p>
      </form>
    </div>
  )
}