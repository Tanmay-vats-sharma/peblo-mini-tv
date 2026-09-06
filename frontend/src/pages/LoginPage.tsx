import { useState, type FormEvent } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { getApiErrorMessage } from '../api/client'
import { useAuth } from '../auth/useAuth'

export function LoginPage() {
  const { hasToken, isLoading, loginWithPassword, user } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  if (hasToken && isLoading) return <main className="status-page">Loading your account…</main>
  if (user) return <Navigate to={user.role === 'viewer' ? '/' : '/admin'} replace />

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setIsSubmitting(true)
    try {
      const currentUser = await loginWithPassword(email, password)
      const requestedPath = (location.state as { from?: string } | null)?.from
      navigate(currentUser.role === 'viewer' ? '/' : requestedPath ?? '/admin', { replace: true })
    } catch (loginError) {
      setError(getApiErrorMessage(loginError))
    } finally {
      setIsSubmitting(false)
    }
  }

  return <main className="auth-page"><form className="login-card" onSubmit={handleSubmit}>
    <p className="eyebrow">Peblo TV CMS</p><h1>Sign in</h1><p className="muted">Use your existing CMS account.</p>
    {error && <p className="form-error" role="alert">{error}</p>}
    <label htmlFor="email">Email</label><input id="email" type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
    <label htmlFor="password">Password</label><input id="password" type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} required />
    <button type="submit" disabled={isSubmitting}>{isSubmitting ? 'Signing in…' : 'Sign in'}</button>
  </form></main>
}
