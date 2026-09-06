import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../auth/useAuth'

export function CmsLayout() {
  const { logout, user } = useAuth()
  return (
    <div className="cms-shell">
      <aside className="cms-sidebar">
        <NavLink className="brand" to="/">Peblo TV</NavLink>
        <p className="role-label">{user?.role} workspace</p>
        <nav aria-label="CMS navigation">
          <NavLink end to="/admin">Dashboard</NavLink>
          <NavLink to="/admin/shows">Shows</NavLink>
          <span aria-disabled="true" className="nav-disabled">Validation (Phase C)</span>
          {user?.role === 'admin' ? <span aria-disabled="true" className="nav-disabled">Publish history (Phase C)</span> : null}
        </nav>
        <div className="sidebar-footer"><span>{user?.email}</span><button className="link-button" type="button" onClick={logout}>Sign out</button></div>
      </aside>
      <main className="cms-main"><header className="cms-topbar"><span>CMS</span><div className="topbar-user"><span>{user?.email} · {user?.role}</span><button className="link-button" type="button" onClick={logout}>Sign out</button></div></header><Outlet /></main>
    </div>
  )
}
