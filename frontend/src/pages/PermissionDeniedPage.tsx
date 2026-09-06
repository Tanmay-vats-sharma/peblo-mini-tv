import { Link } from 'react-router-dom'

export function PermissionDeniedPage() {
  return <main className="status-page"><div><h1>Permission denied</h1><p>Your account does not have access to the CMS.</p><Link to="/">Return to the viewer</Link></div></main>
}
