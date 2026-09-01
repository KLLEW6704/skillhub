import { Navigate, Outlet, useLocation } from 'react-router-dom'
import type { UserRole } from '../../lib/types'
import { useAuth } from './auth-store'

export function ProtectedRoute({ allowedRoles }: { allowedRoles: UserRole[] }) {
  const { user, isLoading } = useAuth()
  const location = useLocation()
  if (isLoading) return <div className="page-state">正在查阅你的成长档案…</div>
  if (!user) return <Navigate to="/login" replace state={{ from: location }} />
  if (!allowedRoles.includes(user.role)) return <Navigate to="/403" replace />
  return <Outlet />
}
