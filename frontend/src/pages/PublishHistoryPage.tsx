import { useQuery } from '@tanstack/react-query'
import { getPublishHistory } from '../api/cms'
import { getApiErrorMessage } from '../api/client'

function formatDateTime(value: string | null): string {
  if (!value) return '—'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString()
}

export function PublishHistoryPage() {
  const historyQuery = useQuery({ queryKey: ['publish-history'], queryFn: getPublishHistory })
  return <section className="content-page"><div className="page-heading"><div><p className="eyebrow">Catalogue quality</p><h1>Publish history</h1></div></div><p className="muted">Newest publish attempts appear first. Blocked attempts did not replace the public catalogue.</p>{historyQuery.isLoading ? <p className="panel-state">Loading publish history…</p> : null}{historyQuery.isError ? <p className="form-error" role="alert">{getApiErrorMessage(historyQuery.error)}</p> : null}{historyQuery.data?.length === 0 ? <p className="panel-state">No catalogue publish attempts have been recorded.</p> : null}{historyQuery.data && historyQuery.data.length > 0 ? <div className="table-wrap"><table className="history-table"><thead><tr><th>Run</th><th>Status</th><th>Started</th><th>Completed</th><th>Triggered by</th><th>Shows</th><th>Episodes</th><th>Errors</th><th>Message</th></tr></thead><tbody>{historyQuery.data.map((run) => <tr key={run.id}><td>#{run.id}</td><td><span className={`status status-${run.status}`}>{run.status}</span></td><td>{formatDateTime(run.started_at)}</td><td>{formatDateTime(run.completed_at)}</td><td>{run.triggered_by ?? '—'}</td><td>{run.show_count}</td><td>{run.episode_count}</td><td>{run.error_count}</td><td>{run.message ?? '—'}</td></tr>)}</tbody></table></div> : null}</section>
}
