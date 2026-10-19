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

  it('shows the landing hero with the app name', () => {
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>,
    )
    expect(screen.getByRole('heading', { name: /Explainable crypto market intelligence/i })).toBeInTheDocument()
    expect(screen.getByText(/TrendCipher fuses news intelligence/i)).toBeInTheDocument()
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