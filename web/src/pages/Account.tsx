import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  api,
  getToken,
  type DeviceEntry,
  type NotifPref,
} from '../lib/api'

const CATEGORY_LABELS: Record<string, string> = {
  general: 'General notifications',
  price_alerts: 'Price alerts',
  scenario_alerts: 'Scenario alerts',
  news_alerts: 'News alerts',
}

export function Account() {
  const authed = Boolean(getToken())
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [roles, setRoles] = useState<string[]>([])
  const [prefs, setPrefs] = useState<NotifPref[]>([])
  const [devices, setDevices] = useState<DeviceEntry[]>([])
  const [alertCount, setAlertCount] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    if (!authed) return
    Promise.all([
      api.authMe(),
      api.getNotificationPreferences(),
      api.getDevices(),
      api.getAlerts(),
    ])
      .then(([me, p, d, a]) => {
        setEmail(me.email)
        setRoles(me.roles ?? [])
        setPrefs(p.preferences)
        setDevices(d.devices)
        setAlertCount(a.alerts.length)
      })
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load account'))
  }, [authed])

  const savePrefs = async () => {
    setSaved(false)
    setError(null)
    try {
      const res = await api.setNotificationPreferences(prefs)
      setPrefs(res.preferences)
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not save preferences')
    }
  }

  const togglePref = (category: string, enabled: boolean) =>
    setPrefs((prev) => prev.map((p) => (p.category === category ? { ...p, enabled } : p)))

  const removeDevice = async (id: number) => {
    setError(null)
    try {
      await api.deleteDevice(id)
      setDevices((prev) => prev.filter((d) => d.id !== id))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not remove device')
    }
  }

  const signOut = () => {
    // clear local tokens; server-side revoke is done at /auth/logout (not exposed)
    localStorage.removeItem('tc_access')
    sessionStorage.removeItem('tc_refresh')
    navigate('/')
  }

  if (!authed) {
    return (
      <section className="placeholder">
        <h2>You are not signed in</h2>
        <p>Sign in to manage your account settings.</p>
      </section>
    )
  }

  return (
    <section className="dashboard">
      <div className="dashboard-header">
        <h2>Account settings</h2>
        {error && <div className="alert alert-error">{error}</div>}
        {saved && <div className="alert" style={{ background: 'rgba(34,197,94,.12)', color: 'var(--c-bull)' }}>Saved</div>}
      </div>

      <div className="card">
        <h3>Profile</h3>
        <p>
          <strong>{email}</strong>{' '}
          <span className="muted small">· {roles.join(', ')}</span>
        </p>
        <p className="muted small">Active alerts: {alertCount}</p>
        <button className="btn btn-outline" onClick={signOut}>
          Sign out
        </button>
      </div>

      <div className="card">
        <h3>Notification preferences</h3>
        {prefs.map((p) => (
          <label key={p.category} className="pref-row">
            <span>{CATEGORY_LABELS[p.category] ?? p.category}</span>
            <input
              type="checkbox"
              checked={p.enabled}
              onChange={(e) => togglePref(p.category, e.target.checked)}
            />
          </label>
        ))}
        <button className="btn btn-primary" onClick={savePrefs}>
          Save preferences
        </button>
      </div>

      <div className="card">
        <h3>Push devices</h3>
        {devices.length === 0 && <p className="muted">No devices registered yet.</p>}
        <table className="data-table">
          <thead>
            <tr>
              <th>Platform</th>
              <th>Provider</th>
              <th>Token</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {devices.map((d) => (
              <tr key={d.id}>
                <td>{d.platform}</td>
                <td>{d.provider}</td>
                <td className="muted small">{d.push_token}</td>
                <td>
                  <button className="btn btn-small btn-outline" onClick={() => removeDevice(d.id)}>
                    Remove
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}