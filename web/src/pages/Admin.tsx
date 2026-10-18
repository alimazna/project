import { useEffect, useState } from 'react'
import {
  api,
  getToken,
  type AdminPlan,
  type AdminUser,
  type PlanVersionEntry,
} from '../lib/api'

type Me = { email?: string; roles?: string[] }

export function Admin() {
  const authed = Boolean(getToken())
  const [me, setMe] = useState<Me>({})
  const [planned, setPlans] = useState<AdminPlan[]>([])
  const [versions, setVersions] = useState<Record<number, PlanVersionEntry[]>>({})
  const [expanded, setExpanded] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [tab, setTab] = useState<'plans' | 'users'>('plans')
  const [users, setUsers] = useState<AdminUser[]>([])
  const [editing, setEditing] = useState<AdminPlan | null>(null)
  const [form, setForm] = useState({
    code: '',
    name: '',
    description: '',
    display_price: '',
    billing_interval: 'monthly',
    sort_order: '0',
    features: '',
    quotas: '{}',
  })

  const isSuper = me.roles?.includes('super_admin') ?? false

  const loadVersions = async (id: number) => {
    try {
      const { versions: v } = await api.planVersions(id)
      setVersions((prev) => ({ ...prev, [id]: v }))
    } catch {
      /* ignore */
    }
  }

  const load = () => {
    api
      .listAdminPlans()
      .then((r) => setPlans(r.items))
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load plans'))
    api
      .listAdminUsers()
      .then((r) => setUsers(r.items))
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load users'))
  }

  const toggleSuspension = async (u: AdminUser) => {
    setError(null)
    try {
      const updated = await api.updateAdminUser(u.id, { is_suspended: !u.is_suspended })
      setUsers((prev) => prev.map((x) => (x.id === u.id ? updated.item : x)))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not update user')
    }
  }

  const setUserRoles = async (u: AdminUser, roles: string[]) => {
    setError(null)
    try {
      const updated = await api.updateAdminUser(u.id, { roles })
      setUsers((prev) => prev.map((x) => (x.id === u.id ? updated.item : x)))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not update roles')
    }
  }

  useEffect(() => {
    if (!authed) return
    api
      .authMe()
      .then((m) => setMe(m))
      .catch(() => {})
    load()
  }, [authed])

  const resetForm = (p?: AdminPlan) => {
    if (p) {
      setForm({
        code: p.code,
        name: p.name,
        description: p.description ?? '',
        display_price: p.display_price,
        billing_interval: p.billing_interval,
        sort_order: String(p.sort_order),
        features: (p.features ?? []).join('\n'),
        quotas: JSON.stringify(p.quotas ?? {}, null, 2),
      })
    } else {
      setForm({ code: '', name: '', description: '', display_price: '', billing_interval: 'monthly', sort_order: '0', features: '', quotas: '{}' })
    }
    setEditing(p ?? null)
  }

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    let quotas: Record<string, unknown>
    try {
      quotas = JSON.parse(form.quotas || '{}')
    } catch {
      setError('quotas must be valid JSON')
      return
    }
    const features = form.features.split('\n').map((s) => s.trim()).filter(Boolean)
    const payload = {
      name: form.name,
      description: form.description || null,
      display_price: form.display_price || 'Free',
      billing_interval: form.billing_interval,
      sort_order: Number(form.sort_order) || 0,
      features,
      quotas,
    }
    try {
      if (editing) {
        await api.updateAdminPlan(editing.id, payload)
      } else {
        await api.createAdminPlan({ ...payload, code: form.code })
      }
      resetForm()
      load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not save plan')
    }
  }

  const archive = async (p: AdminPlan) => {
    setError(null)
    try {
      await api.archiveAdminPlan(p.id)
      load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not archive plan')
    }
  }

  if (!authed) {
    return (
      <section className="placeholder">
        <h2>You are not signed in</h2>
        <p>Sign in to manage plans.</p>
      </section>
    )
  }

  if (!isSuper) {
    return (
      <section className="placeholder">
        <h2>Admin only</h2>
        <p>Plans management is restricted to super administrators.</p>
      </section>
    )
  }

  return (
    <section className="dashboard">
      <div className="dashboard-header">
        <h2>Admin</h2>
        {error && <div className="alert alert-error">{error}</div>}
      </div>

      <div className="tabs">
        <button className={`tab ${tab === 'plans' ? 'tab-active' : ''}`} onClick={() => setTab('plans')}>
          Plans
        </button>
        <button className={`tab ${tab === 'users' ? 'tab-active' : ''}`} onClick={() => setTab('users')}>
          Users ({users.length})
        </button>
      </div>

      {tab === 'users' && (
        <div className="card">
          <h3>Users</h3>
          <table className="data-table">
            <thead>
              <tr>
                <th>Email</th>
                <th>Roles</th>
                <th>State</th>
                <th>Plan</th>
                <th>Last login</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  <td>{u.email}</td>
                  <td>
                    <select
                      value={u.roles.includes('super_admin') ? 'super_admin' : u.roles.includes('admin') ? 'admin' : 'user'}
                      onChange={(e) => setUserRoles(u, e.target.value === 'user' ? [] : [e.target.value])}
                      disabled={me.email === u.email}
                    >
                      <option value="user">user</option>
                      <option value="admin">admin</option>
                      <option value="super_admin">super_admin</option>
                    </select>
                  </td>
                  <td>
                    <span className={`badge ${u.is_suspended ? 'badge-unknown' : u.is_active ? 'badge-ok' : 'badge-unknown'}`}>
                      {u.is_suspended ? 'Suspended' : u.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td>{u.plan ?? '—'}</td>
                  <td className="muted small">{u.last_login_at ? new Date(u.last_login_at).toLocaleString() : '—'}</td>
                  <td>
                    {me.email !== u.email && (
                      <button className="btn btn-small btn-outline" onClick={() => toggleSuspension(u)}>
                        {u.is_suspended ? 'Reinstate' : 'Suspend'}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'plans' && (
      <>
      <form className="card" onSubmit={submit}>
        <h3>{editing ? `Edit plan — ${editing.code}` : 'Create a plan'}</h3>
        <div className="alert-form">
          {!editing && (
            <label>
              Code
              <input required value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} placeholder="pro" />
            </label>
          )}
          <label>
            Name
            <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Pro Trader" />
          </label>
          <label>
            Display price
            <input value={form.display_price} onChange={(e) => setForm({ ...form, display_price: e.target.value })} placeholder="$19" />
          </label>
          <label>
            Billing
            <select value={form.billing_interval} onChange={(e) => setForm({ ...form, billing_interval: e.target.value })}>
              <option value="none">One-time</option>
              <option value="monthly">Monthly</option>
              <option value="yearly">Yearly</option>
            </select>
          </label>
          <label>
            Sort order
            <input type="number" value={form.sort_order} onChange={(e) => setForm({ ...form, sort_order: e.target.value })} />
          </label>
        </div>
        <label>
          Description
          <input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
        </label>
        <label>
          Features (one per line)
          <textarea rows={3} value={form.features} onChange={(e) => setForm({ ...form, features: e.target.value })} />
        </label>
        <label>
          Quotas (JSON)
          <textarea rows={3} value={form.quotas} onChange={(e) => setForm({ ...form, quotas: e.target.value })} />
        </label>
        <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.6rem' }}>
          <button className="btn btn-primary" type="submit">
            {editing ? 'Save changes' : 'Create plan'}
          </button>
          {editing && (
            <button className="btn btn-outline" type="button" onClick={() => resetForm()}>
              Cancel
            </button>
          )}
        </div>
      </form>

      <div className="card">
        <h3>All plans</h3>
        <table className="data-table">
          <thead>
            <tr>
              <th>Code</th>
              <th>Name</th>
              <th>Price</th>
              <th>State</th>
              <th>Quotas</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {planned.map((p) => (
              <tr key={p.id}>
                <td>{p.code}</td>
                <td>{p.name}</td>
                <td>{p.display_price}</td>
                <td>
                  <span className={`badge ${p.is_active ? 'badge-ok' : 'badge-unknown'}`}>
                    {p.is_archived ? 'Archived' : p.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td className="muted small">{p.quotas ? JSON.stringify(p.quotas) : '—'}</td>
                <td>
                  <button className="btn btn-small" onClick={() => resetForm(p)}>
                    Edit
                  </button>{' '}
                  <button
                    className="btn btn-small btn-outline"
                    onClick={() => {
                      const next = expanded === p.id ? null : p.id
                      setExpanded(next)
                      if (next != null) loadVersions(p.id)
                    }}
                  >
                    {expanded === p.id ? 'Hide versions' : 'Versions'}
                  </button>{' '}
                  {!p.is_archived && (
                    <button className="btn btn-small btn-outline" onClick={() => archive(p)}>
                      Archive
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {expanded != null && versions[expanded] && (
          <div className="version-list">
            <h4>Version history</h4>
            {versions[expanded].map((v) => (
              <p key={v.id} className="muted small">
                v{v.id} — {v.name} ({v.display_price}) · quotas {JSON.stringify(v.quotas)} · by user {v.changed_by ?? '?'} ·{' '}
                {v.created_at ? new Date(v.created_at).toLocaleString() : '—'}
              </p>
            ))}
          </div>
        )}
      </div>
      </>
      )}
    </section>
  )
}