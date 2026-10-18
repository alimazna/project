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

export interface Me {
  id?: number
  email: string
  display_name?: string | null
  roles?: string[]
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

export interface ScenarioDecision {
  signal: string
  vote: number
  weight: number
  aligned: number
  value?: Record<string, unknown>
  reason: string
}

export interface ScenarioDetail {
  id?: number
  symbol: string
  direction: 'BULLISH' | 'BEARISH' | 'NEUTRAL'
  status: string
  timeframe: string
  alignment_score: number
  risk_reward: number | null
  entry_low: number | null
  entry_high: number | null
  stop_loss: number | null
  take_profits: number[]
  invalidation: Record<string, unknown>
  rule_version: string
  evidence: {
    signals_evaluated?: number
    bullish?: number
    bearish?: number
    neutral?: number
    weighted_alignment?: number
  }
  decisions: ScenarioDecision[]
  last_close?: number
  generated_at?: string
  created_at?: string
}

export interface Watchlist {
  id: number
  name: string
  is_default: boolean
  symbols: string[]
}

export interface UserAlert {
  id: number
  symbol: string
  kind: string
  value: number | null
  is_active: boolean
  cooldown_minutes: number
  last_fired_at: string | null
  created_at: string | null
}

export interface NotifPref {
  category: string
  channel: string
  enabled: boolean
}

export interface DeviceEntry {
  id: number
  platform: string
  provider: string
  push_token: string
  created_at: string | null
}

export interface AlertDeliveryEntry {
  id: number
  alert_id: number
  symbol: string | null
  channel: string
  status: string
  created_at: string | null
}

export interface BacktestResult {
  results: { index: number; symbol: string; direction: string; entry: number; exit_price: number; pnl_pct: number; alignment: number; rule_version: string; hold_bars: number }[]
  stats: {
    trades: number
    wins: number
    losses: number
    winrate_pct: number
    avg_pnl_pct: number
    total_pnl_pct: number
    hold_bars: number
  }
  config: { symbol: string; hold_bars: number; start: number; end: number }
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
  runAnalysis: (symbol: string, interval: string, limit = 200, withNews = true) =>
    api.post<{ scenario: ScenarioDetail; saved_scenario_id: number | null }>(
      `/analysis/run?symbol=${encodeURIComponent(symbol)}&interval=${interval}&limit=${limit}&with_news=${withNews}&persist=true`,
    ),
  getScenarios: (symbol?: string, limit = 10) =>
    api.get<{ scenarios: ScenarioDetail[] }>(
      `/analysis/scenarios?limit=${limit}${symbol ? `&symbol=${encodeURIComponent(symbol)}` : ''}`,
    ),
  getScenario: (id: number) => api.get<{ scenario: ScenarioDetail }>(`/analysis/scenarios/${id}`),
  runBacktest: (symbol: string, interval: string, limit = 400, holdBars = 24) =>
    api.get<BacktestResult>(
      `/analysis/backtest?symbol=${encodeURIComponent(symbol)}&interval=${interval}&limit=${limit}&hold_bars=${holdBars}`,
    ),
  getWatchlists: () => api.get<{ watchlists: Watchlist[] }>('/watchlists'),
  createWatchlist: (name: string, symbols: string[]) =>
    api.post<{ watchlist: Watchlist }>('/watchlists', { name, symbols }),
  updateWatchlist: (id: number, patch: { name?: string; symbols?: string[] }) =>
    api.put<{ watchlist: Watchlist }>(`/watchlists/${id}`, patch),
  deleteWatchlist: (id: number) => api.del(`/watchlists/${id}`),
  getAlerts: (active?: boolean) => api.get<{ alerts: UserAlert[] }>(`/alerts${active != null ? `?active=${active}` : ''}`),
  createAlert: (symbol: string, kind: string, value?: number, cooldownMinutes = 30) =>
    api.post<{ alert: UserAlert }>('/alerts', {
      symbol,
      kind,
      value: value ?? null,
      cooldown_minutes: cooldownMinutes,
    }),
  updateAlert: (id: number, patch: Partial<{ is_active: boolean; value: number; cooldown_minutes: number; symbol: string }>) =>
    api.put<{ alert: UserAlert }>(`/alerts/${id}`, patch),
  deleteAlert: (id: number) => api.del(`/alerts/${id}`),
  evaluateAlert: (id: number) => api.post<{ fired: boolean; evaluated: boolean }>(`/alerts/${id}/evaluate`),
  getAlertDeliveries: (limit = 20) =>
    api.get<{ deliveries: AlertDeliveryEntry[] }>(`/alerts/deliveries?limit=${limit}`),
  getNotificationPreferences: () => api.get<{ preferences: NotifPref[] }>('/notification-preferences'),
  setNotificationPreferences: (prefs: NotifPref[]) =>
    api.put<{ preferences: NotifPref[] }>('/notification-preferences', prefs),
  getDevices: () => api.get<{ devices: DeviceEntry[] }>('/devices'),
  registerDevice: (platform: string, pushToken: string, provider = 'expo') =>
    api.post<{ device: { id: number; platform: string; provider: string } }>('/devices', {
      platform,
      push_token: pushToken,
      provider,
    }),
  deleteDevice: (id: number) => api.del(`/devices/${id}`),
  authMe: () => api.get<Me>('/auth/me'),
}