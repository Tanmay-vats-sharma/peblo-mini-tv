import { Navigate, Outlet, useLocation } from 'react-router-dom'
import type { UserRole } from '../api/auth'
import { useAuth } from './useAuth'

export function ProtectedRoute({ allowedRoles }: { allowedRoles: UserRole[] }) {
  const { hasToken, isLoading, user } = useAuth()
  const location = useLocation()
  if (!hasToken) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  if (isLoading) return <main className="status-page">Loading your account…</main>
  if (!user) return <Navigate to="/login" replace />
  if (!allowedRoles.includes(user.role)) return <Navigate to="/forbidden" replace />
  return <Outlet />
}
