import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { getArtworkUrl, getCatalogue, getEpisodeLanguages, formatDuration, type CatalogueEpisode, type CatalogueShow } from '../api/catalogue'
import { getApiErrorMessage } from '../api/client'

function EpisodeCard({ episode, thumbnail }: { episode: CatalogueEpisode; thumbnail: string | null }) {
  const languages = getEpisodeLanguages(episode)
  return <article className="episode-card"><div className="episode-thumb">{thumbnail ? <img src={thumbnail} alt="" loading="lazy" /> : <span>{String(episode.episode_number).padStart(2, '0')}</span>}</div><div className="episode-copy"><div className="episode-heading"><h3>{episode.title}</h3><span>{formatDuration(episode.duration_seconds)}</span></div><p>{episode.description || 'No episode description available.'}</p><div className="episode-meta"><span>Languages: {languages.length > 0 ? languages.join(', ').toUpperCase() : 'Unavailable'}</span>{episode.video_url ? <a className="watch-button" href={episode.video_url} target="_blank" rel="noreferrer">Watch</a> : <span className="unavailable">Video unavailable</span>}</div></div></article>
}

function findShow(sections: { shows: CatalogueShow[] }[], slug: string): CatalogueShow | undefined {
  return sections.flatMap((section) => section.shows).find((show) => show.slug === slug)
}

export function ShowDetailsPage() {
  const { slug } = useParams<{ slug: string }>()
  const catalogueQuery = useQuery({ queryKey: ['catalogue'], queryFn: getCatalogue })
  if (catalogueQuery.isLoading) return <div className="viewer-state">Loading show details...</div>
  if (catalogueQuery.isError) return <div className="viewer-state viewer-error"><h1>Show unavailable</h1><p>{getApiErrorMessage(catalogueQuery.error)}</p></div>
  const show = slug ? findShow(catalogueQuery.data?.sections ?? [], slug) : undefined
  if (!show) return <div className="viewer-state"><h1>Show not found</h1><p>This title is not part of the current published catalogue.</p><Link className="viewer-button viewer-button-primary" to="/catalog">Back to catalogue</Link></div>

  const banner = getArtworkUrl(show.artworks.banner ?? show.artworks.poster)
  const poster = getArtworkUrl(show.artworks.poster ?? show.artworks.thumbnail)
  const thumbnail = getArtworkUrl(show.artworks.thumbnail ?? show.artworks.poster)
  const seasons = [...show.seasons].filter((season) => season.season_number !== 0).sort((a, b) => a.season_number - b.season_number)

  return <div className="show-details">
    <section className="details-hero" style={banner ? { backgroundImage: `linear-gradient(90deg, rgba(246, 249, 251, .98) 0%, rgba(246, 249, 251, .82) 48%, rgba(246, 249, 251, .18) 100%), url(${banner})` } : undefined}><div className="details-hero-copy"><Link className="back-link" to="/catalog">Back to catalogue</Link><p className="viewer-kicker">{show.section}</p><h1>{show.title}</h1><div className="details-meta">{show.release_year ? <span>{show.release_year}</span> : null}<span>{show.categories.join(' / ')}</span></div><p>{show.description || 'No description available.'}</p></div></section>
    <section className="details-body">{poster ? <img className="details-poster" src={poster} alt={`${show.title} poster`} /> : null}<div className="season-list">{seasons.length === 0 ? <div className="viewer-state"><h2>Episodes coming soon</h2><p>This show has no published episodes yet.</p></div> : seasons.map((season) => <section className="season-block" key={season.season_number}><div className="season-heading"><h2>Season {season.season_number}{season.title ? `: ${season.title}` : ''}</h2><span>{season.episodes.length} episode{season.episodes.length === 1 ? '' : 's'}</span></div>{season.description ? <p className="muted">{season.description}</p> : null}<div className="episode-list">{season.episodes.map((episode) => <EpisodeCard key={episode.content_group} episode={episode} thumbnail={thumbnail} />)}</div></section>)}</div></section>
  </div>
}
