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

export interface TickerEntry {
  symbol: string
  last_price: number
  high_24h: number | null
  low_24h: number | null
  volume_24h: number | null
  change_24h_pct: number | null
  fetched_at: string
}

export interface CandleEntry {
  open_time: string
  close_time: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  closed: boolean
}

export interface NewsEntry {
  id: number
  source: string
  url: string
  title: string
  summary: string | null
  author: string | null
  published_at: string | null
  sentiment: string
  relevance_score: number
  assets: string
}

export interface SymbolEntry {
  symbol: string
  base: string
  quote: string
  display_name: string | null
  provider: string
}

export interface HealthResult {
  status: string
  providers: { provider: string; status: string; last_success_at?: string | null; last_error?: string | null; error_count?: number }[]
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'POST', body: JSON.stringify(body ?? {}) }),
  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'PUT', body: JSON.stringify(body ?? {}) }),
  del: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
  getTickers: () => api.get<{ tickers: TickerEntry[] }>('/market/tickers'),
  getCandles: (symbol: string, interval: string, limit = 200) =>
    api.get<{ symbol: string; interval: string; candles: CandleEntry[] }>(
      `/market/candles/${encodeURIComponent(symbol)}?interval=${interval}&limit=${limit}`,
    ),
  getNews: (limit = 30) => api.get<{ articles: NewsEntry[] }>(`/market/news?limit=${limit}`),
  getSymbols: () => api.get<{ symbols: SymbolEntry[] }>('/market/symbols'),
  getHealth: () => api.get<HealthResult>('/health'),
}