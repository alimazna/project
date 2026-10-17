// Thin API client for the TrendCipher backend.
// All authoritative market/analysis data flows through this client.

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

let accessToken: string | null =
  typeof window !== 'undefined' ? window.localStorage.getItem('tc_access') : null

export function setToken(token: string | null) {
  accessToken = token
  if (typeof window !== 'undefined') {
    if (token) window.localStorage.setItem('tc_access', token)
    else window.localStorage.removeItem('tc_access')
  }
}

export function getToken() {
  return accessToken
}

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  }
  if (accessToken) headers.Authorization = `Bearer ${accessToken}`

  const resp = await fetch(`${API_BASE}${path}`, { ...options, headers })
  if (!resp.ok) {
    let message = `Request failed (${resp.status})`
    try {
      const body = await resp.json()
      if (body?.error?.message) message = body.error.message
      else if (body?.detail) message = String(body.detail)
    } catch {
      /* keep default message */
    }
    throw new ApiError(resp.status, message)
  }
  return resp.json() as Promise<T>
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'POST', body: JSON.stringify(body ?? {}) }),
  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'PUT', body: JSON.stringify(body ?? {}) }),
  del: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
}