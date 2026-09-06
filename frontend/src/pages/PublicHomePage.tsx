import { Link } from 'react-router-dom'
import { useAuth } from '../auth/useAuth'

export function PublicHomePage() {
  const { user } = useAuth()
  const canUseCms = user?.role === 'admin' || user?.role === 'editor'
  return <main className="public-page"><nav className="public-nav"><span className="brand">Peblo TV</span><Link to={canUseCms ? '/admin' : '/login'}>{canUseCms ? 'CMS' : 'CMS sign in'}</Link></nav><section className="public-intro"><p className="eyebrow">Video catalogue</p><h1>The viewer arrives in Phase D.</h1><p className="muted">Public catalogue search, filters, show details, seasons, and episode playback will be implemented after the CMS workflow.</p></section></main>
}
