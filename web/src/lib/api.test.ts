import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError, api, setToken } from './api'

describe('api client', () => {
  it('exposes an ApiError type', () => {
    const err = new ApiError(401, 'nope')
    expect(err.status).toBe(401)
    expect(err.message).toBe('nope')
  })

  it('setToken persists to localStorage', () => {
    setToken('abc123')
    expect(window.localStorage.getItem('tc_access')).toBe('abc123')
    setToken(null)
    expect(window.localStorage.getItem('tc_access')).toBeNull()
  })
})

function mockFetchOnce(body: unknown) {
  const fn = vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    json: async () => body,
  })
  vi.stubGlobal('fetch', fn)
  // jsdom exposes fetch on window; ensure both point at the same mock.
  vi.stubGlobal('window', { ...window, fetch: fn })
  return fn
}

afterEach(() => {
  vi.unstubAllGlobals()
  setToken(null)
})

describe('analysis api clients', () => {
  it('runAnalysis POSTs to /analysis/run with symbol+interval', async () => {
    const fetchMock = mockFetchOnce({
      scenario: { direction: 'BULLISH', symbol: 'BTC/USD', decisions: [] },
      saved_scenario_id: 7,
    })
    await api.runAnalysis('BTC/USD', '1h', 120, true)
    const [url, init] = fetchMock.mock.calls[0]
    expect(String(url)).toContain('/analysis/run')
    expect(String(url)).toContain('symbol=BTC%2FUSD')
    expect(String(url)).toContain('interval=1h')
    expect(init.method).toBe('POST')
  })

  it('getScenarios requests the scenarios list', async () => {
    const fetchMock = mockFetchOnce({ scenarios: [] })
    await api.getScenarios('BTC/USD', 10)
    const [url] = fetchMock.mock.calls[0]
    expect(String(url)).toContain('/analysis/scenarios')
    expect(String(url)).toContain('symbol=BTC%2FUSD')
  })

  it('runBacktest requests backtest stats', async () => {
    const fetchMock = mockFetchOnce({ results: [], stats: { trades: 0 } })
    await api.runBacktest('ETH/USD', '1h', 400, 24)
    const [url] = fetchMock.mock.calls[0]
    expect(String(url)).toContain('/analysis/backtest')
    expect(String(url)).toContain('hold_bars=24')
  })
})