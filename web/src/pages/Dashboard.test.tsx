import { beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { Dashboard } from './Dashboard'

// Hoisted mock factories — usable inside vi.mock modules (which are hoisted).
const mocks = vi.hoisted(() => ({
  getHealth: vi.fn(),
  getSymbols: vi.fn(),
  getTickers: vi.fn(),
  getNews: vi.fn(),
  getCandles: vi.fn(),
  runAnalysis: vi.fn(),
}))

// The chart renders on <canvas> (lightweight-charts) — jsdom has no real canvas;
// stub it so the test exercises the surrounding dashboard logic only.
vi.mock('../components/CandleChart', () => ({
  CandleChart: () => <div data-testid="mock-chart" />,
}))

vi.mock('../lib/api', () => ({
  getToken: () => 'mock-token',
  api: {
    getHealth: mocks.getHealth,
    getSymbols: mocks.getSymbols,
    getTickers: mocks.getTickers,
    getNews: mocks.getNews,
    getCandles: mocks.getCandles,
    runAnalysis: mocks.runAnalysis,
  },
}))

const tickers = [
  {
    symbol: 'BTC/USD',
    last_price: 65000,
    high_24h: 66000,
    low_24h: 64000,
    volume_24h: 1000,
    change_24h_pct: 0.02,
    fetched_at: '2026-01-01T00:00:00Z',
  },
]

const scenario = {
  id: 1,
  symbol: 'BTC/USD',
  direction: 'BULLISH',
  status: 'ready',
  timeframe: '1h',
  alignment_score: 0.8,
  rule_version: 'v1',
  last_close: 65000,
  entry_low: 64000,
  entry_high: 64500,
  stop_loss: 62000,
  take_profits: [67000, 69000],
  risk_reward: 2,
  decisions: [{ signal: 'trend_ma', vote: 1, weight: 0.5, reason: 'above MA' }],
}

beforeEach(() => {
  vi.clearAllMocks()
  mocks.getHealth.mockResolvedValue({ status: 'ok', providers: [] })
  mocks.getSymbols.mockResolvedValue({
    symbols: [{ symbol: 'BTC/USD', base: 'BTC', quote: 'USD', display_name: null, provider: 'kraken' }],
  })
  mocks.getTickers.mockResolvedValue({ tickers })
  mocks.getNews.mockResolvedValue({
    articles: [
      { id: 1, source: 'CoinTelegraph', url: 'https://x.test', title: 'Bitcoin rises on ETF flows', summary: null, author: null, published_at: null, sentiment: 'positive', relevance_score: 0.8, assets: 'BTC' },
    ],
  })
  mocks.getCandles.mockResolvedValue({
    candles: [
      { open_time: '2026-01-01T00:00:00Z', close_time: '2026-01-01T01:00:00Z', open: 1, high: 2, low: 1, close: 2, volume: 10, closed: true },
    ],
  })
  mocks.runAnalysis.mockResolvedValue({ scenario, saved_scenario_id: 1 })
})

describe('Dashboard', () => {
  it('shows the signed-in dashboard with market overview and tickers', async () => {
    const { container } = render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>,
    )
    expect(await screen.findByText('Market Overview')).toBeInTheDocument()
    expect(screen.getByText('BTC/USD')).toBeInTheDocument()
    const symbolChip = container.querySelector('.ticker-chip .ticker-symbol')
    expect(symbolChip?.textContent).toBe('BTC/USD')
    const priceChip = container.querySelector('.ticker-chip .ticker-price')
    expect(priceChip?.textContent).toBe('65,000')
  })

  it('renders the explainable scenario card with drivers after analysis', async () => {
    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>,
    )
    expect(await screen.findByText('Scenario — explainable')).toBeInTheDocument()
    // "Why?" section renders each decision signal + reason.
    expect(await screen.findByText(/trend ma/i)).toBeInTheDocument()
    expect(screen.getByText(/above MA/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Re-run/i })).toBeInTheDocument()
  })

  it('supports switching trading intervals from the segmented control', async () => {
    const { container } = render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>,
    )
    // initial interval is 1h — that button is active
    const dayBtn = await screen.findByRole('button', { name: '1d' })
    expect(container.querySelector('.segmented')).toBeInTheDocument()
    const hourBtn = screen.getByRole('button', { name: '1h' })
    expect(hourBtn.classList.contains('segmented-active')).toBe(true)
    expect(dayBtn.classList.contains('segmented-active')).toBe(false)

    fireEvent.click(dayBtn)
    await waitFor(() => {
      expect(screen.getByRole('button', { name: '1d' }).classList.contains('segmented-active')).toBe(true)
      expect(screen.getByRole('button', { name: '1h' }).classList.contains('segmented-active')).toBe(false)
    })
    expect(mocks.getCandles).toHaveBeenLastCalledWith('BTC/USD', '1d', 100)
  })
})