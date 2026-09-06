import { api } from './client'

export type CatalogueSectionName = 'featured' | 'series' | 'minisodes' | 'songs'

export interface CatalogueEpisode {
  content_group: string
  title: string
  episode_number: number
  description: string | null
  duration_seconds: number | null
  video_url: string | null
  languages: string[] | string
}

export interface CatalogueSeason {
  season_number: number
  title: string | null
  description: string | null
  episodes: CatalogueEpisode[]
}

export interface CatalogueShow {
  id: number
  title: string
  slug: string
  description: string | null
  section: CatalogueSectionName
  categories: string[]
  release_year: number | null
  artworks: Record<string, string | null>
  seasons: CatalogueSeason[]
}

export interface CatalogueSection {
  section: CatalogueSectionName
  shows: CatalogueShow[]
}

export interface CatalogueDocument {
  generated_at: string
  version: number
  sections: CatalogueSection[]
}

export interface CatalogueSearchItem {
  show_id: number
  show_title: string
  show_slug: string
  description: string | null
  section: CatalogueSectionName
  categories: string[]
  release_year: number | null
  season_number: number
  season_title: string | null
  content_group: string
  episode_title: string
  episode_number: number
  episode_description: string | null
  duration_seconds: number | null
  video_url: string | null
  languages: string[]
  artworks: Record<string, string | null>
}

export interface CatalogueSearchResponse {
  items: CatalogueSearchItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
  query: string | null
  category: string | null
  language: string | null
  section: CatalogueSectionName | null
}

export interface CatalogueSearchParams {
  q?: string
  category?: string
  language?: string
  section?: CatalogueSectionName
  page?: number
  page_size?: number
}

export async function getCatalogue(): Promise<CatalogueDocument> {
  const response = await api.get<CatalogueDocument>('/catalog')
  return response.data
}

export async function searchCatalogue(
  params: CatalogueSearchParams,
): Promise<CatalogueSearchResponse> {
  const response = await api.get<CatalogueSearchResponse>('/catalog/search', {
    params: {
      q: params.q || undefined,
      category: params.category || undefined,
      language: params.language || undefined,
      section: params.section || undefined,
      page: params.page ?? 1,
      page_size: params.page_size ?? 12,
    },
  })
  return response.data
}

export function getArtworkUrl(path: string | null | undefined): string | null {
  if (!path) return null
  if (path.startsWith('http://') || path.startsWith('https://')) return path
  return path
}

export function getEpisodeCount(show: CatalogueShow): number {
  return (show.seasons ?? []).reduce(
    (total, season) => total + (season.episodes ?? []).length,
    0,
  )
}

export function getEpisodeLanguages(episode: CatalogueEpisode): string[] {
  return Array.isArray(episode.languages) ? episode.languages : [episode.languages]
}

export function formatDuration(seconds: number | null): string {
  if (!seconds) return 'Runtime unavailable'
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return `${minutes}m ${String(remainingSeconds).padStart(2, '0')}s`
}
