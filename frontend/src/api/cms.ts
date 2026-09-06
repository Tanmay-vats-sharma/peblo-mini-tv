import { api } from './client'

export type ShowSection = 'featured' | 'series' | 'minisodes' | 'songs'
export type EpisodeLanguage = 'en' | 'hi'
export type EpisodeStatus = 'draft' | 'published'

export interface Show {
  id: number
  title: string
  slug: string
  description: string | null
  section: ShowSection | null
  categories: string[]
  release_year: number | null
  is_published: boolean
  created_at: string
  updated_at: string
}

export interface ShowPayload {
  title: string
  slug: string
  description: string | null
  section: ShowSection | null
  categories: string[]
  release_year: number | null
  is_published: boolean
}

export interface ListShowsParams {
  search?: string
  section?: ShowSection
  isPublished?: boolean
  skip?: number
  limit?: number
}

export interface Season {
  id: number
  show_id: number
  season_number: number
  title: string
  description: string | null
  created_at: string
  updated_at: string
}

export interface SeasonPayload {
  season_number: number
  title: string
  description: string | null
}

export interface Episode {
  id: number
  seed_episode_id: string
  season_id: number
  title: string
  episode_number: number
  content_group: string
  language: EpisodeLanguage
  status: EpisodeStatus
  description: string | null
  video_url: string | null
  duration_seconds: number | null
}

export interface EpisodePayload {
  seed_episode_id?: string
  title: string
  episode_number: number
  content_group: string
  language: EpisodeLanguage
  status: EpisodeStatus
  description: string | null
  video_url: string | null
  duration_seconds: number | null
}

export interface UploadedArtwork {
  id: number
  show_id: number
  artwork_type: 'POSTER' | 'BANNER' | 'THUMBNAIL'
  original_filename: string
  storage_key: string
  image_url: string | null
  mime_type: string
  width: number
  height: number
  file_size_bytes: number
}

interface ArtworkUploadResponse {
  success: boolean
  message: string
  artwork: UploadedArtwork
}

export async function listShows(params: ListShowsParams): Promise<Show[]> {
  const response = await api.get<Show[]>('/admin/shows', {
    params: {
      search: params.search || undefined,
      section: params.section,
      is_published: params.isPublished,
      skip: params.skip ?? 0,
      limit: params.limit ?? 10,
    },
  })
  return response.data
}

export async function getShow(showId: number): Promise<Show> {
  const response = await api.get<Show>(`/admin/shows/${showId}`)
  return response.data
}

export async function createShow(payload: ShowPayload): Promise<Show> {
  const response = await api.post<Show>('/admin/shows', payload)
  return response.data
}

export async function updateShow(showId: number, payload: ShowPayload): Promise<Show> {
  const response = await api.patch<Show>(`/admin/shows/${showId}`, payload)
  return response.data
}

export async function deleteShow(showId: number): Promise<void> {
  await api.delete(`/admin/shows/${showId}`)
}

export async function listSeasons(showId: number, includeTrailers: boolean): Promise<Season[]> {
  const response = await api.get<Season[]>(`/admin/shows/${showId}/seasons`, {
    params: { include_trailers: includeTrailers },
  })
  return response.data
}

export async function createSeason(showId: number, payload: SeasonPayload): Promise<Season> {
  const response = await api.post<Season>(`/admin/shows/${showId}/seasons`, payload)
  return response.data
}

export async function updateSeason(seasonId: number, payload: SeasonPayload): Promise<Season> {
  const response = await api.patch<Season>(`/admin/seasons/${seasonId}`, payload)
  return response.data
}

export async function deleteSeason(seasonId: number): Promise<void> {
  await api.delete(`/admin/seasons/${seasonId}`)
}

export async function getSeason(seasonId: number): Promise<Season> {
  const response = await api.get<Season>(`/admin/seasons/${seasonId}`)
  return response.data
}

export async function listEpisodes(seasonId: number): Promise<Episode[]> {
  const response = await api.get<Episode[]>(`/admin/seasons/${seasonId}/episodes`)
  return response.data
}

export async function createEpisode(seasonId: number, payload: EpisodePayload): Promise<Episode> {
  const response = await api.post<Episode>(`/admin/seasons/${seasonId}/episodes`, payload)
  return response.data
}

export async function updateEpisode(episodeId: number, payload: EpisodePayload): Promise<Episode> {
  const { seed_episode_id: _seedEpisodeId, ...updatePayload } = payload
  const response = await api.patch<Episode>(`/admin/episodes/${episodeId}`, updatePayload)
  return response.data
}

export async function deleteEpisode(episodeId: number): Promise<void> {
  await api.delete(`/admin/episodes/${episodeId}`)
}

export async function uploadArtwork(
  showId: number,
  artworkType: 'poster' | 'banner' | 'thumbnail',
  file: File,
  onProgress: (percent: number) => void,
): Promise<UploadedArtwork> {
  const formData = new FormData()
  formData.append('show_id', String(showId))
  formData.append('artwork_type', artworkType)
  formData.append('file', file)
  const response = await api.post<ArtworkUploadResponse>('/admin/artworks/upload', formData, {
    onUploadProgress: (event) => {
      if (event.total) onProgress(Math.round((event.loaded / event.total) * 100))
    },
  })
  return response.data.artwork
}

export function artworkUrl(imageUrl: string | null): string | null {
  if (!imageUrl) return null
  const baseUrl = String(api.defaults.baseURL ?? '')
  if (!baseUrl.startsWith('http')) return imageUrl
  return new URL(imageUrl, baseUrl).toString()
}
