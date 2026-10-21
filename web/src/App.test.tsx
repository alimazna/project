import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { App } from './App'

describe('App shell', () => {
  it('renders the default brand split (Trend<Cipher>) in the header', () => {
    const { container } = render(
      <MemoryRouter>
        <App />
      </MemoryRouter>,
    )
    const brand = container.querySelector('.brand') as HTMLAnchorElement
    expect(brand).toBeInTheDocument()
    expect(brand.textContent).toBe('TrendCipher')
    expect(brand.querySelector('span')?.textContent).toBe('Cipher')
  })

  it('shows the WEP marketing hero with products and pricing cards', () => {
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>,
    )
    expect(screen.getByRole('heading', { name: /Maximize Market Opportunity/i })).toBeInTheDocument()
    expect(screen.getByText(/predictive statistical platform/i)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Download App' })).toBeInTheDocument()
    expect(screen.getAllByRole('link', { name: 'Go Pro' }).length).toBeGreaterThan(0)
    expect(screen.getByRole('link', { name: 'Get Basic' })).toBeInTheDocument()
    expect(screen.getByText('Pricing Plans')).toBeInTheDocument()
    expect(screen.getByText('$0')).toBeInTheDocument()
    expect(screen.getByText('$199')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Pro' })).toBeInTheDocument()
  })

  it('renders the pricing page (nav + section) for the plans route', () => {
    render(
      <MemoryRouter initialEntries={['/plans']}>
        <App />
      </MemoryRouter>,
    )
    const pricingLinks = screen.getAllByText(/Pricing/i)
    expect(pricingLinks.length).toBeGreaterThan(0)
  })
})