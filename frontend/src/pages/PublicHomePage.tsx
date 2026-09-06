import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { getArtworkUrl, getCatalogue } from '../api/catalogue'
import { getApiErrorMessage } from '../api/client'
import { ShowCard } from '../components/ShowCard'

const sectionLabels: Record<string, string> = { featured: 'Featured', series: 'Series', minisodes: 'Minisodes', songs: 'Songs' }

export function PublicHomePage() {
  const catalogueQuery = useQuery({ queryKey: ['catalogue'], queryFn: getCatalogue })
  if (catalogueQuery.isLoading) return <div className="viewer-state">Loading the catalogue...</div>
  if (catalogueQuery.isError) return <div className="viewer-state viewer-error"><h1>Catalogue unavailable</h1><p>{getApiErrorMessage(catalogueQuery.error)}</p></div>

  const sections = catalogueQuery.data?.sections ?? []
  const featured = sections.find((section) => section.section === 'featured')?.shows[0] ?? sections.flatMap((section) => section.shows)[0]
  const heroArtwork = getArtworkUrl(featured?.artworks.banner ?? featured?.artworks.poster)

  return <div className="viewer-home">
    {featured ? <section className="viewer-hero" style={heroArtwork ? { backgroundImage: `linear-gradient(90deg, rgba(246, 249, 251, .98) 0%, rgba(246, 249, 251, .86) 44%, rgba(246, 249, 251, .18) 100%), url(${heroArtwork})` } : undefined}>
      <div className="hero-copy"><p className="viewer-kicker">{sectionLabels[featured.section] ?? featured.section}</p><h1>{featured.title}</h1><p>{featured.description || 'A new story is waiting to be discovered.'}</p><div className="hero-actions"><Link className="viewer-button viewer-button-primary" to={`/catalog/shows/${featured.slug}`}>View details</Link><Link className="viewer-button viewer-button-quiet" to="/catalog">Browse catalogue</Link></div></div>
    </section> : <section className="viewer-empty-hero"><p className="viewer-kicker">Peblo TV</p><h1>Your next story starts here.</h1><p>The published catalogue is currently empty.</p></section>}
    <div className="viewer-rows">
      {sections.map((section) => section.shows.length > 0 ? <section className="viewer-row" key={section.section}><div className="row-heading"><h2>{sectionLabels[section.section] ?? section.section}</h2><Link to={`/catalog?section=${section.section}`}>See all</Link></div><div className="show-row">{section.shows.map((show) => <ShowCard key={show.id} show={show} />)}</div></section> : null)}
    </div>
  </div>
}
