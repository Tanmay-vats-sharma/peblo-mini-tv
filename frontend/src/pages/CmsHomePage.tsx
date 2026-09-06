import { useAuth } from '../auth/useAuth'

export function CmsHomePage() {
  const { user } = useAuth()
  return <section><p className="eyebrow">Content management</p><h1>Welcome{user ? `, ${user.email}` : ''}</h1><p className="muted">Shows, seasons, episodes, artwork, validation, and publishing will be added in the next CMS phases.</p></section>
}
