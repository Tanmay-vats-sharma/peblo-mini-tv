import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import { Link, Navigate, useParams } from 'react-router-dom'
import { createSeason, deleteSeason, getShow, listSeasons, updateSeason, type Season, type SeasonPayload } from '../api/cms'
import { getApiErrorMessage } from '../api/client'

const blankSeason: SeasonPayload = { season_number: 1, title: '', description: null }

export function SeasonManagementPage() {
  const { showId: rawShowId } = useParams()
  const showId = rawShowId ? Number(rawShowId) : null
  const [includeTrailers, setIncludeTrailers] = useState(false)
  const [editingSeason, setEditingSeason] = useState<Season | null>(null)
  const [seasonNumber, setSeasonNumber] = useState(String(blankSeason.season_number))
  const [title, setTitle] = useState(blankSeason.title)
  const [description, setDescription] = useState('')
  const [clientError, setClientError] = useState<string | null>(null)
  const queryClient = useQueryClient()
  const showQuery = useQuery({ queryKey: ['show', showId], queryFn: () => getShow(showId as number), enabled: showId !== null && Number.isInteger(showId) })
  const seasonsQuery = useQuery({ queryKey: ['seasons', showId, includeTrailers], queryFn: () => listSeasons(showId as number, includeTrailers), enabled: showId !== null && Number.isInteger(showId) })
  const saveMutation = useMutation({ mutationFn: (payload: SeasonPayload) => editingSeason ? updateSeason(editingSeason.id, payload) : createSeason(showId as number, payload), onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['seasons', showId] }); resetForm() } })
  const deleteMutation = useMutation({ mutationFn: deleteSeason, onSuccess: () => queryClient.invalidateQueries({ queryKey: ['seasons', showId] }) })
  if (!showId || !Number.isInteger(showId)) return <Navigate to="/admin/shows" replace />

  function resetForm() { setEditingSeason(null); setSeasonNumber(String(blankSeason.season_number)); setTitle(''); setDescription(''); setClientError(null) }
  function editSeason(season: Season) { setEditingSeason(season); setSeasonNumber(String(season.season_number)); setTitle(season.title); setDescription(season.description ?? ''); setClientError(null) }
  function submitSeason(event: FormEvent<HTMLFormElement>) { event.preventDefault(); const number = Number(seasonNumber); if (!Number.isInteger(number) || number < 0) return setClientError('Season number must be a whole number of 0 or greater.'); if (!title.trim()) return setClientError('Season title is required.'); setClientError(null); saveMutation.mutate({ season_number: number, title: title.trim(), description: description.trim() || null }) }
  function removeSeason(season: Season) { if (window.confirm(`Delete ${season.title} and all of its episodes?`)) deleteMutation.mutate(season.id) }

  return <section className="content-page"><div className="page-heading"><div><p className="eyebrow">{showQuery.data?.title ?? 'Show'}</p><h1>Seasons</h1></div><Link to="/admin/shows">Back to shows</Link></div>{showQuery.isError || seasonsQuery.isError ? <p className="form-error" role="alert">{getApiErrorMessage(showQuery.error ?? seasonsQuery.error)}</p> : null}<label className="checkbox-label trailer-toggle"><input type="checkbox" checked={includeTrailers} onChange={(event) => setIncludeTrailers(event.target.checked)} /> Include trailer season (season 0)</label>{seasonsQuery.isLoading ? <p className="panel-state">Loading seasons…</p> : null}{seasonsQuery.data?.length === 0 ? <p className="panel-state">No seasons found. Create the first season below.</p> : null}{seasonsQuery.data?.map((season) => <article className="resource-card" key={season.id}><div><h2>{season.season_number === 0 ? 'Trailer season (0)' : `Season ${season.season_number}`}: {season.title}</h2><p className="muted">{season.description || 'No description.'}</p></div><div className="row-actions"><Link to={`/admin/seasons/${season.id}/episodes`}>Episodes</Link><button type="button" onClick={() => editSeason(season)}>Edit</button><button className="danger-button" type="button" disabled={deleteMutation.isPending} onClick={() => removeSeason(season)}>Delete</button></div></article>)}<form className="editor-form" onSubmit={submitSeason}><h2>{editingSeason ? `Edit ${editingSeason.title}` : 'Create season'}</h2>{clientError || saveMutation.isError || deleteMutation.isError ? <p className="form-error" role="alert">{clientError ?? getApiErrorMessage(saveMutation.error ?? deleteMutation.error)}</p> : null}<div className="form-grid"><label>Season number<input type="number" min="0" step="1" value={seasonNumber} onChange={(event) => setSeasonNumber(event.target.value)} required /></label><label>Title<input value={title} maxLength={255} onChange={(event) => setTitle(event.target.value)} required /></label><label className="full-width">Description<textarea value={description} onChange={(event) => setDescription(event.target.value)} /></label></div><div className="form-actions"><button className="primary-button" type="submit" disabled={saveMutation.isPending}>{saveMutation.isPending ? 'Saving…' : editingSeason ? 'Update season' : 'Create season'}</button>{editingSeason ? <button type="button" onClick={resetForm}>Cancel edit</button> : null}</div></form></section>
}
