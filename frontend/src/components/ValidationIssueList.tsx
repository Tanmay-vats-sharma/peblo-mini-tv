import type { ValidationIssue } from '../api/cms'

interface ValidationIssueListProps {
  title: string
  issues: ValidationIssue[]
  tone: 'error' | 'warning'
  emptyMessage: string
}

export function ValidationIssueList({ title, issues, tone, emptyMessage }: ValidationIssueListProps) {
  return <section className={`issue-section issue-section-${tone}`}><h2>{title} <span className="issue-count">{issues.length}</span></h2>{issues.length === 0 ? <p className="panel-state">{emptyMessage}</p> : <div className="table-wrap"><table className="issue-table"><thead><tr><th>Code</th><th>Message</th><th>Entity</th><th>Field</th><th>Details</th></tr></thead><tbody>{issues.map((issue, index) => <tr key={`${issue.code}-${issue.entity_type}-${issue.entity_id ?? 'none'}-${issue.field ?? 'none'}-${index}`}><td><code>{issue.code}</code></td><td>{issue.message}</td><td>{issue.entity_type}{issue.entity_id !== null ? ` #${issue.entity_id}` : ''}</td><td>{issue.field ?? '—'}</td><td>{Object.keys(issue.details).length > 0 ? <pre>{JSON.stringify(issue.details, null, 2)}</pre> : '—'}</td></tr>)}</tbody></table></div>}</section>
}
