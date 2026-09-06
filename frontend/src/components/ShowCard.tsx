import { Link } from 'react-router-dom'
import { getArtworkUrl, getEpisodeCount, type CatalogueShow } from '../api/catalogue'

export function ShowCard({ show }: { show: CatalogueShow }) {
  const artwork = getArtworkUrl(show.artworks.poster ?? show.artworks.thumbnail ?? show.artworks.banner)
  const episodeCount = getEpisodeCount(show)
  return <Link className="show-card" to={`/catalog/shows/${show.slug}`}>
    <div className="show-card-art">
      {artwork ? <img src={artwork} alt={`${show.title} poster`} loading="lazy" /> : <span>{show.title.slice(0, 1)}</span>}
    </div>
    <div className="show-card-copy"><h3>{show.title}</h3><span>{episodeCount} episode{episodeCount === 1 ? '' : 's'}{show.release_year ? ` · ${show.release_year}` : ''}</span></div>
  </Link>
}
