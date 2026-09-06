import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { deleteShow, listShows, type ShowSection } from '../api/cms'
import { getApiErrorMessage } from '../api/client'

const PAGE_SIZE = 10
const sections: ShowSection[] = ['featured', 'series', 'minisodes', 'songs']

export function ShowsPage() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [section, setSection] = useState<ShowSection | ''>('')
  const [status, setStatus] = useState<'all' | 'published' | 'draft'>('all')
  const [page, setPage] = useState(0)
  const showsQuery = useQuery({
    queryKey: ['shows', { search, section, status, page }],
    queryFn: () => listShows({
      search,
      section: section || undefined,
      isPublished: status === 'all' ? undefined : status === 'published',
      skip: page * PAGE_SIZE,
      limit: PAGE_SIZE,
    }),
  })
  const deleteMutation = useMutation({
    mutationFn: deleteShow,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['shows'] }),
  })

  function setFilter(update: () => void) {
    update()
    setPage(0)
  }

  function requestDelete(showId: number, title: string) {
    if (window.confirm(`Delete “${title}”? Its seasons, episodes, and artwork will also be removed.`)) {
      deleteMutation.mutate(showId)
    }
  }

  return (
    <section className="content-page">
      <div className="page-heading"><div><p className="eyebrow">Content library</p><h1>Shows</h1></div><Link className="primary-button" to="/admin/shows/new">Create show</Link></div>
      <div className="filters" aria-label="Show filters">
        <label>Search<input value={search} onChange={(event) => setFilter(() => setSearch(event.target.value))} placeholder="Search title" /></label>
        <label>Section<select value={section} onChange={(event) => setFilter(() => setSection(event.target.value as ShowSection | ''))}><option value="">All sections</option>{sections.map((item) => <option key={item} value={item}>{item}</option>)}</select></label>
        <label>Status<select value={status} onChange={(event) => setFilter(() => setStatus(event.target.value as typeof status))}><option value="all">All statuses</option><option value="published">Published</option><option value="draft">Draft</option></select></label>
      </div>
      {deleteMutation.isError ? <p className="form-error" role="alert">{getApiErrorMessage(deleteMutation.error)}</p> : null}
      {showsQuery.isLoading ? <p className="panel-state">Loading shows…</p> : null}
      {showsQuery.isError ? <p className="form-error" role="alert">{getApiErrorMessage(showsQuery.error)}</p> : null}
      {showsQuery.data && showsQuery.data.length === 0 ? <p className="panel-state">No shows match these filters.</p> : null}
      {showsQuery.data && showsQuery.data.length > 0 ? <div className="table-wrap"><table><thead><tr><th>Title</th><th>Section</th><th>Status</th><th>Year</th><th><span className="sr-only">Actions</span></th></tr></thead><tbody>{showsQuery.data.map((show) => <tr key={show.id}><td><strong>{show.title}</strong><small>{show.slug}</small></td><td>{show.section ?? 'Unassigned'}</td><td><span className={`status status-${show.is_published ? 'published' : 'draft'}`}>{show.is_published ? 'Published' : 'Draft'}</span></td><td>{show.release_year ?? '—'}</td><td className="row-actions"><Link to={`/admin/shows/${show.id}/edit`}>Edit</Link><Link to={`/admin/shows/${show.id}/seasons`}>Seasons</Link><button type="button" className="danger-button" disabled={deleteMutation.isPending} onClick={() => requestDelete(show.id, show.title)}>Delete</button></td></tr>)}</tbody></table></div> : null}
      <div className="pagination"><button type="button" disabled={page === 0 || showsQuery.isLoading} onClick={() => setPage((current) => current - 1)}>Previous</button><span>Page {page + 1}</span><button type="button" disabled={!showsQuery.data || showsQuery.data.length < PAGE_SIZE || showsQuery.isLoading} onClick={() => setPage((current) => current + 1)}>Next</button></div>
    </section>
  )
}
