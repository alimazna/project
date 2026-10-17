import { describe, expect, it } from 'vitest'
import { ApiError, setToken } from './api'

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