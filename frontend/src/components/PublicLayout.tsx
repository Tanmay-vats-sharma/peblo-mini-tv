import { useState, type FormEvent } from 'react'
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/useAuth'

export function PublicLayout() {
  const { user } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const [query, setQuery] = useState(new URLSearchParams(location.search).get('q') ?? '')
  const canUseCms = user?.role === 'admin' || user?.role === 'editor'

  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const value = query.trim()
    navigate(value ? `/catalog/search?q=${encodeURIComponent(value)}` : '/catalog')
  }

  return <div className="viewer-shell">
    <header className="viewer-nav">
      <Link className="viewer-brand" to="/">PEBLO <span>TV</span></Link>
      <nav className="viewer-links" aria-label="Public navigation">
        <NavLink end to="/">Home</NavLink>
        <NavLink to="/catalog">Catalogue</NavLink>
      </nav>
      <form className="viewer-search" onSubmit={submitSearch} role="search">
        <label className="sr-only" htmlFor="viewer-search-input">Search catalogue</label>
        <input id="viewer-search-input" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search shows and episodes" />
        <button type="submit" aria-label="Search catalogue">Search</button>
      </form>
      <Link className="viewer-account" to={canUseCms ? '/admin' : '/login'}>{canUseCms ? 'CMS' : 'Sign in'}</Link>
    </header>
    <main><Outlet /></main>
    <footer className="viewer-footer">Peblo TV <span>Published catalogue</span></footer>
  </div>
}
