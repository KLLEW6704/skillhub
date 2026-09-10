import { describe, expect, it } from 'vitest'
import { dashboardFor, postLoginPath } from './role-routes'

describe('role-aware workspace routing', () => {
  it.each([
    ['student', '/student'],
    ['requester', '/requester'],
    ['reviewer', '/reviewer'],
    ['admin', '/admin'],
  ] as const)('sends %s to its own dashboard', (role, dashboard) => {
    expect(dashboardFor(role)).toBe(dashboard)
    expect(postLoginPath(role, '/reviewer')).toBe(dashboard)
  })

  it('restores a deep link only when it belongs to the signed-in role', () => {
    expect(postLoginPath('student', '/student/portfolios')).toBe('/student/portfolios')
    expect(postLoginPath('requester', '/student/portfolios')).toBe('/requester')
  })
})
