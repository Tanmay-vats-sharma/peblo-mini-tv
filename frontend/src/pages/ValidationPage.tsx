import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { getValidationReport, publishCatalogue, type PublishResult } from '../api/cms'
import { getApiErrorMessage } from '../api/client'
import { useAuth } from '../auth/useAuth'
import { ValidationIssueList } from '../components/ValidationIssueList'

export function ValidationPage() {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const [publishResult, setPublishResult] = useState<PublishResult | null>(null)
  const validationQuery = useQuery({ queryKey: ['validation-report'], queryFn: getValidationReport })
  const publishMutation = useMutation({
    mutationFn: publishCatalogue,
    onSuccess: (result) => {
      setPublishResult(result)
      queryClient.invalidateQueries({ queryKey: ['validation-report'] })
      queryClient.invalidateQueries({ queryKey: ['publish-history'] })
    },
  })
  const isAdmin = user?.role === 'admin'

  function requestPublish() {
    if (!isAdmin) return
    if (window.confirm('Publish the current catalogue? Validation will run first, and invalid data will block publishing.')) {
      publishMutation.mutate()
    }
  }

  return <section className="content-page"><div className="page-heading"><div><p className="eyebrow">Catalogue quality</p><h1>Validation report</h1></div><div className="publish-control">{isAdmin ? <button className="primary-button" type="button" disabled={publishMutation.isPending} onClick={requestPublish}>{publishMutation.isPending ? 'Publishing…' : 'Publish catalogue'}</button> : <><button className="primary-button" type="button" disabled>Publish catalogue</button><span className="field-note">Only administrators can publish. The backend will also reject editor publish requests.</span></>}</div></div><p className="muted">Publishing is blocked while validation errors exist. This report reflects the current database and does not change invalid records.</p>
    {validationQuery.isLoading ? <p className="panel-state">Loading validation report…</p> : null}
    {validationQuery.isError ? <p className="form-error" role="alert">{getApiErrorMessage(validationQuery.error)}</p> : null}
    {validationQuery.data ? <><div className={`validation-summary ${validationQuery.data.valid ? 'validation-valid' : 'validation-invalid'}`}><strong>{validationQuery.data.valid ? 'Valid catalogue' : 'Catalogue has blocking errors'}</strong><span>{validationQuery.data.error_count} error{validationQuery.data.error_count === 1 ? '' : 's'}</span><span>{validationQuery.data.warning_count} warning{validationQuery.data.warning_count === 1 ? '' : 's'}</span></div><ValidationIssueList title="Blocking errors" issues={validationQuery.data.errors} tone="error" emptyMessage="No blocking validation errors." /><ValidationIssueList title="Warnings" issues={validationQuery.data.warnings} tone="warning" emptyMessage="No validation warnings." /></> : null}
    {publishMutation.isError ? <p className="form-error" role="alert">Publish request failed: {getApiErrorMessage(publishMutation.error)}</p> : null}
    {publishResult ? <PublishResultPanel result={publishResult} /> : null}
  </section>
}

function PublishResultPanel({ result }: { result: PublishResult }) {
  const statusTitle = result.status === 'succeeded' ? 'Catalogue published' : result.status === 'blocked' ? 'Publishing blocked' : 'Publishing failed'
  return <section className={`publish-result publish-result-${result.status}`} aria-live="polite"><h2>{statusTitle}</h2><p>{result.message}</p><dl><div><dt>Status</dt><dd>{result.status}</dd></div><div><dt>Errors</dt><dd>{result.error_count}</dd></div><div><dt>Warnings</dt><dd>{result.warnings.length}</dd></div>{result.status === 'succeeded' ? <><div><dt>Shows</dt><dd>{result.show_count}</dd></div><div><dt>Episodes</dt><dd>{result.episode_count}</dd></div><div><dt>Version</dt><dd>{result.version ?? '—'}</dd></div></> : null}</dl>{result.status === 'blocked' ? <p className="blocked-explanation">Invalid data was not published; the existing public catalogue was left unchanged.</p> : null}{result.errors.length > 0 ? <ValidationIssueList title="Publish validation errors" issues={result.errors} tone="error" emptyMessage="" /> : null}{result.warnings.length > 0 ? <ValidationIssueList title="Publish warnings" issues={result.warnings} tone="warning" emptyMessage="" /> : null}</section>
}
