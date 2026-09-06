import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import { Link, Navigate, useNavigate, useParams } from 'react-router-dom'
import { createShow, getShow, updateShow, type Show, type ShowPayload, type ShowSection } from '../api/cms'
import { getApiErrorMessage } from '../api/client'
import { ArtworkUploadPanel } from '../components/ArtworkUploadPanel'

const sections: ShowSection[] = ['featured', 'series', 'minisodes', 'songs']
const emptyShow: ShowPayload = { title: '', slug: '', description: null, section: null, categories: [], release_year: null, is_published: false }

export function ShowEditorPage() {
  const { showId: rawShowId } = useParams()
  const showId = rawShowId ? Number(rawShowId) : null
  const showQuery = useQuery({ queryKey: ['show', showId], queryFn: () => getShow(showId as number), enabled: showId !== null && Number.isInteger(showId) })
  if (rawShowId && (!showId || !Number.isInteger(showId))) return <Navigate to="/admin/shows" replace />
  if (showQuery.isLoading) return <p className="panel-state">Loading show…</p>
  if (showQuery.isError) return <section className="content-page"><p className="form-error" role="alert">{getApiErrorMessage(showQuery.error)}</p><Link to="/admin/shows">Back to shows</Link></section>
  return <ShowForm key={showQuery.data?.id ?? 'new'} show={showQuery.data} />
}

function ShowForm({ show }: { show: Show | undefined }) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [title, setTitle] = useState(show?.title ?? emptyShow.title)
  const [slug, setSlug] = useState(show?.slug ?? emptyShow.slug)
  const [description, setDescription] = useState(show?.description ?? '')
  const [section, setSection] = useState<ShowSection | ''>(show?.section ?? '')
  const [categories, setCategories] = useState(show?.categories.join(', ') ?? '')
  const [releaseYear, setReleaseYear] = useState(show?.release_year?.toString() ?? '')
  const [isPublished, setIsPublished] = useState(show?.is_published ?? false)
  const [clientError, setClientError] = useState<string | null>(null)
  const saveMutation = useMutation({
    mutationFn: (payload: ShowPayload) => show ? updateShow(show.id, payload) : createShow(payload),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['shows'] }); navigate('/admin/shows') },
  })

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const normalizedCategories = [...new Set(categories.split(',').map((item) => item.trim().toLowerCase()).filter(Boolean))]
    const parsedYear = releaseYear.trim() ? Number(releaseYear) : null
    if (!title.trim() || !slug.trim()) return setClientError('Title and slug are required.')
    if (parsedYear !== null && (!Number.isInteger(parsedYear) || parsedYear < 1900 || parsedYear > 2100)) return setClientError('Release year must be between 1900 and 2100.')
    if (isPublished && !section) return setClientError('Published shows must have a section.')
    setClientError(null)
    saveMutation.mutate({ title: title.trim(), slug: slug.trim(), description: description.trim() || null, section: section || null, categories: normalizedCategories, release_year: parsedYear, is_published: isPublished })
  }

  return <section className="content-page"><div className="page-heading"><div><p className="eyebrow">Content library</p><h1>{show ? 'Edit show' : 'Create show'}</h1></div><Link to="/admin/shows">Back to shows</Link></div><form className="editor-form" onSubmit={handleSubmit}>
    {(clientError || saveMutation.isError) ? <p className="form-error" role="alert">{clientError ?? getApiErrorMessage(saveMutation.error)}</p> : null}
    <div className="form-grid"><label>Title<input value={title} onChange={(event) => setTitle(event.target.value)} maxLength={255} required /></label><label>Slug<input value={slug} onChange={(event) => setSlug(event.target.value)} maxLength={255} required /></label><label className="full-width">Description<textarea value={description} onChange={(event) => setDescription(event.target.value)} /></label><label>Section<select value={section} onChange={(event) => setSection(event.target.value as ShowSection | '')}><option value="">Unassigned</option>{sections.map((item) => <option key={item} value={item}>{item}</option>)}</select></label><label>Release year<input type="number" min="1900" max="2100" value={releaseYear} onChange={(event) => setReleaseYear(event.target.value)} /></label><label className="full-width">Categories <span className="field-note">Comma-separated</span><input value={categories} onChange={(event) => setCategories(event.target.value)} placeholder="family, adventure" /></label><label className="checkbox-label"><input type="checkbox" checked={isPublished} onChange={(event) => setIsPublished(event.target.checked)} /> Published</label></div>
    <div className="form-actions"><button className="primary-button" type="submit" disabled={saveMutation.isPending}>{saveMutation.isPending ? 'Saving…' : 'Save show'}</button></div>
  </form>{show ? <ArtworkUploadPanel showId={show.id} /> : <p className="field-note">Save the show before uploading artwork.</p>}</section>
}
