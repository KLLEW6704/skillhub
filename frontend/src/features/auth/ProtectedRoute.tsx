import { Navigate, Outlet, useLocation } from 'react-router-dom'
import type { UserRole } from '../../lib/types'
import { dashboardFor } from './role-routes'
import { useAuth } from './use-auth'

export function ProtectedRoute({ allowedRoles }: { allowedRoles: UserRole[] }) {
  const { user, isLoading } = useAuth()
  const location = useLocation()
  if (isLoading) return <div className="page-state">正在查阅你的成长档案…</div>
  if (!user) return <Navigate to="/login" replace state={{ from: location }} />
  if (!allowedRoles.includes(user.role)) return <Navigate to={dashboardFor(user.role)} replace />
  return <Outlet />
}
