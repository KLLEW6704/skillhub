import type { UserRole } from '../../lib/types'

const dashboards: Record<UserRole, string> = {
  student: '/student',
  requester: '/requester',
  reviewer: '/reviewer',
  admin: '/admin',
}

export function dashboardFor(role: UserRole) {
  return dashboards[role]
}

export function postLoginPath(role: UserRole, requestedPath?: string) {
  const dashboard = dashboardFor(role)
  if (requestedPath === dashboard || requestedPath?.startsWith(`${dashboard}/`)) {
    return requestedPath
  }
  return dashboard
}
