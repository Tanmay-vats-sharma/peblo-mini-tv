import { useQuery } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { getCatalogue, searchCatalogue, type CatalogueSearchItem, type CatalogueSectionName, type CatalogueShow } from '../api/catalogue'
import { getApiErrorMessage } from '../api/client'
import { ShowCard } from '../components/ShowCard'

const sections: CatalogueSectionName[] = ['featured', 'series', 'minisodes', 'songs']

function uniqueShows(items: CatalogueSearchItem[]) {
  const shows = new Map<number, CatalogueSearchItem>()
  items.forEach((item) => shows.set(item.show_id, item))
  return [...shows.values()].sort((a, b) => a.show_title.localeCompare(b.show_title))
}

export function CataloguePage({ searchOnly = false }: { searchOnly?: boolean }) {
  const [searchParams, setSearchParams] = useSearchParams()
  const [query, setQuery] = useState(searchParams.get('q') ?? '')
  const [debouncedQuery, setDebouncedQuery] = useState(query)
  const section = searchParams.get('section') ?? ''
  const category = searchParams.get('category') ?? ''
  const language = searchParams.get('language') ?? ''
  const page = Number(searchParams.get('page') ?? '1') || 1

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedQuery(query.trim()), 350)
    return () => window.clearTimeout(timer)
  }, [query])

  useEffect(() => {
    const next = new URLSearchParams(searchParams)
    if (debouncedQuery) next.set('q', debouncedQuery); else next.delete('q')
    next.delete('page')
    if (next.toString() !== searchParams.toString()) setSearchParams(next, { replace: true })
  }, [debouncedQuery, searchParams, setSearchParams])

  const hasFilters = searchOnly || Boolean(debouncedQuery || category || language || section)
  const catalogueQuery = useQuery({
    queryKey: ['catalogue'],
    queryFn: getCatalogue,
    enabled: !hasFilters,
  })
  const searchQuery = useQuery({
    queryKey: ['catalogue-search', debouncedQuery, category, language, section, page],
    queryFn: () => searchCatalogue({ q: debouncedQuery, category, language, section: section as CatalogueSectionName || undefined, page }),
    enabled: hasFilters,
  })
  const catalogueShows = catalogueQuery.data?.sections.flatMap((item) => item.shows) ?? []
  const searchShows: CatalogueShow[] = uniqueShows(searchQuery.data?.items ?? []).map((item) => ({
    id: item.show_id,
    title: item.show_title,
    slug: item.show_slug,
    description: item.description,
    section: item.section,
    categories: item.categories,
    release_year: item.release_year,
    artworks: item.artworks,
    seasons: [],
  }))
  const shows = hasFilters ? searchShows : catalogueShows

  function updateFilter(key: string, value: string) {
    const next = new URLSearchParams(searchParams)
    if (value) next.set(key, value); else next.delete(key)
    next.delete('page')
    setSearchParams(next)
  }

  const isLoading = catalogueQuery.isLoading || searchQuery.isLoading
  const error = catalogueQuery.error ?? searchQuery.error
  const resultCount = hasFilters ? searchQuery.data?.total : catalogueShows.length

  return (
    <section className="catalogue-page">
      {/* Header Section */}
      <div className="catalogue-header">
        <div className="catalogue-header-content">
          <span className="catalogue-kicker">🌟 Explore Peblo TV</span>
          <h1 className="catalogue-title">{searchOnly ? '🔍 Search Results' : '📺 Catalogue'}</h1>
          <p className="catalogue-subtitle">Find published shows, episodes, and stories worth returning to.</p>
        </div>
        {resultCount !== undefined && (
          <div className="result-count-badge">
            <span className="result-count-number">{resultCount}</span>
            <span className="result-count-label">show{resultCount === 1 ? '' : 's'}</span>
          </div>
        )}
      </div>

      {/* Filters Section */}
      <div className="filters-container">
        <div className="filters-grid">
          <div className="filter-group">
            <label className="filter-label">🔎 Search</label>
            <input
              className="filter-input"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Show or episode title..."
            />
          </div>

          <div className="filter-group">
            <label className="filter-label">📂 Section</label>
            <select
              className="filter-select"
              value={section}
              onChange={(event) => updateFilter('section', event.target.value)}
            >
              <option value="">All sections</option>
              {sections.map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label className="filter-label">🏷️ Category</label>
            <input
              className="filter-input"
              value={category}
              onChange={(event) => updateFilter('category', event.target.value)}
              placeholder="e.g. comedy, adventure"
            />
          </div>

          <div className="filter-group">
            <label className="filter-label">🌐 Language</label>
            <select
              className="filter-select"
              value={language}
              onChange={(event) => updateFilter('language', event.target.value)}
            >
              <option value="">All languages</option>
              <option value="en">🇬🇧 English</option>
              <option value="hi">🇮🇳 Hindi</option>
            </select>
          </div>
        </div>
      </div>

      {/* State Messages */}
      {isLoading && (
        <div className="state-message state-loading">
          <div className="state-icon">⏳</div>
          <h2>Searching the catalogue...</h2>
          <p>We're finding the best shows for you!</p>
        </div>
      )}

      {error && (
        <div className="state-message state-error">
          <div className="state-icon">😕</div>
          <h2>Could not load results</h2>
          <p>{getApiErrorMessage(error)}</p>
        </div>
      )}

      {!isLoading && !error && shows.length === 0 && (
        <div className="state-message state-empty">
          <div className="state-icon">🎈</div>
          <h2>No matches yet</h2>
          <p>Try another title, category, language, or section.</p>
        </div>
      )}

      {/* Shows Grid */}
      {shows.length > 0 && (
        <div className="shows-grid">
          {shows.map((show) => (
            <ShowCard key={show.id} show={show} />
          ))}
        </div>
      )}

      {/* Pagination */}
      {searchQuery.data && searchQuery.data.total_pages > 1 && (
        <div className="pagination-container">
          <button
            className="pagination-button"
            disabled={page <= 1}
            onClick={() => updateFilter('page', String(page - 1))}
          >
            ← Previous
          </button>
          <span className="pagination-info">
            Page {page} of {searchQuery.data.total_pages}
          </span>
          <button
            className="pagination-button"
            disabled={page >= searchQuery.data.total_pages}
            onClick={() => updateFilter('page', String(page + 1))}
          >
            Next →
          </button>
        </div>
      )}

      <style>{`
        .catalogue-page {
          max-width: 1400px;
          margin: 0 auto;
          padding: 2rem 1.5rem;
          background: linear-gradient(135deg, #fff9f0 0%, #ffeef8 100%);
          min-height: 100vh;
          font-family: 'Segoe UI', 'Comic Sans MS', 'Chalkboard SE', cursive, sans-serif;
        }

        /* Header */
        .catalogue-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          flex-wrap: wrap;
          gap: 1.5rem;
          margin-bottom: 2.5rem;
          padding: 2rem 2.5rem;
          background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
          border-radius: 30px;
          box-shadow: 0 8px 32px rgba(252, 182, 159, 0.3);
          border: 3px solid #ffb08c;
        }

        .catalogue-header-content {
          flex: 1;
        }

        .catalogue-kicker {
          display: inline-block;
          font-size: 1.1rem;
          font-weight: 600;
          color: #7c3a1e;
          background: rgba(255, 255, 255, 0.7);
          padding: 0.3rem 1rem;
          border-radius: 50px;
          margin-bottom: 0.5rem;
          backdrop-filter: blur(4px);
          border: 2px solid #ff9a76;
        }

        .catalogue-title {
          font-size: 3rem;
          font-weight: 800;
          margin: 0.25rem 0;
          background: linear-gradient(135deg, #e85d04, #dc2f02);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          text-shadow: 2px 2px 0px rgba(220, 47, 2, 0.1);
        }

        .catalogue-subtitle {
          font-size: 1.2rem;
          color: #5a3a2a;
          font-weight: 500;
          margin: 0.25rem 0 0 0;
          background: rgba(255, 255, 255, 0.5);
          padding: 0.3rem 1.2rem;
          border-radius: 50px;
          display: inline-block;
          backdrop-filter: blur(2px);
        }

        .result-count-badge {
          background: linear-gradient(135deg, #ff6b6b, #ee5a24);
          padding: 0.8rem 1.8rem;
          border-radius: 60px;
          display: flex;
          align-items: baseline;
          gap: 0.3rem;
          box-shadow: 0 4px 16px rgba(238, 90, 36, 0.4);
          border: 3px solid white;
          align-self: center;
        }

        .result-count-number {
          font-size: 2.5rem;
          font-weight: 800;
          color: white;
          line-height: 1;
        }

        .result-count-label {
          font-size: 1.1rem;
          font-weight: 600;
          color: white;
          opacity: 0.9;
        }

        /* Filters */
        .filters-container {
          background: white;
          border-radius: 24px;
          padding: 1.8rem 2rem;
          margin-bottom: 2.5rem;
          box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
          border: 3px solid #fdd7c0;
        }

        .filters-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
          gap: 1.5rem;
          align-items: end;
        }

        .filter-group {
          display: flex;
          flex-direction: column;
          gap: 0.4rem;
        }

        .filter-label {
          font-weight: 700;
          font-size: 0.9rem;
          color: #6b3a2a;
          letter-spacing: 0.3px;
        }

        .filter-input,
        .filter-select {
          padding: 0.7rem 1rem;
          border: 3px solid #fdd7c0;
          border-radius: 16px;
          font-size: 1rem;
          font-family: inherit;
          background: #fefaf8;
          transition: all 0.2s ease;
          color: #2d1b12;
          font-weight: 500;
        }

        .filter-input:focus,
        .filter-select:focus {
          outline: none;
          border-color: #ff8a5c;
          box-shadow: 0 0 0 4px rgba(255, 138, 92, 0.2);
          background: white;
        }

        .filter-input::placeholder {
          color: #bfa092;
          font-weight: 400;
        }

        .filter-select {
          cursor: pointer;
          appearance: none;
          background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%236b3a2a' d='M6 8L1 3h10z'/%3E%3C/svg%3E");
          background-repeat: no-repeat;
          background-position: right 1rem center;
          padding-right: 2.5rem;
        }

        /* State Messages */
        .state-message {
          text-align: center;
          padding: 4rem 2rem;
          border-radius: 30px;
          background: white;
          box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
          margin: 2rem 0;
          border: 3px dashed #fdd7c0;
        }

        .state-icon {
          font-size: 4rem;
          margin-bottom: 0.5rem;
          display: block;
        }

        .state-message h2 {
          font-size: 2rem;
          margin: 0.5rem 0;
          color: #2d1b12;
        }

        .state-message p {
          font-size: 1.1rem;
          color: #6b4a3a;
          margin: 0;
        }

        .state-loading {
          border-color: #ffb07c;
          background: linear-gradient(135deg, #fff5ee, #ffede6);
        }

        .state-error {
          border-color: #ff6b6b;
          background: linear-gradient(135deg, #fff0f0, #ffe6e6);
        }

        .state-empty {
          border-color: #ffd93d;
          background: linear-gradient(135deg, #fffbee, #fff8e0);
        }

        /* Shows Grid */
        .shows-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
          gap: 2rem;
          margin: 2.5rem 0;
        }

        /* Pagination */
        .pagination-container {
          display: flex;
          justify-content: center;
          align-items: center;
          gap: 1.5rem;
          margin: 3rem 0 1rem;
          padding: 1.2rem;
          background: white;
          border-radius: 60px;
          box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
          border: 3px solid #fdd7c0;
        }

        .pagination-button {
          padding: 0.6rem 1.8rem;
          border: none;
          border-radius: 50px;
          font-size: 1rem;
          font-weight: 700;
          cursor: pointer;
          transition: all 0.2s ease;
          background: linear-gradient(135deg, #ff8a5c, #ff6b35);
          color: white;
          font-family: inherit;
        }

        .pagination-button:hover:not(:disabled) {
          transform: scale(1.05);
          box-shadow: 0 4px 16px rgba(255, 107, 53, 0.4);
        }

        .pagination-button:disabled {
          opacity: 0.4;
          cursor: not-allowed;
          transform: none;
        }

        .pagination-info {
          font-weight: 600;
          font-size: 1.1rem;
          color: #4a2a1a;
          background: #fff5ee;
          padding: 0.3rem 1.5rem;
          border-radius: 50px;
        }

        /* Responsive */
        @media (max-width: 768px) {
          .catalogue-page {
            padding: 1rem;
          }

          .catalogue-header {
            flex-direction: column;
            padding: 1.5rem;
          }

          .catalogue-title {
            font-size: 2.2rem;
          }

          .result-count-badge {
            align-self: flex-start;
          }

          .filters-grid {
            grid-template-columns: 1fr;
            gap: 1rem;
          }

          .shows-grid {
            grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
            gap: 1.2rem;
          }

          .pagination-container {
            flex-wrap: wrap;
            gap: 0.8rem;
            border-radius: 30px;
            padding: 1rem;
          }
        }

        @media (max-width: 480px) {
          .catalogue-title {
            font-size: 1.8rem;
          }

          .catalogue-subtitle {
            font-size: 1rem;
          }

          .shows-grid {
            grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
            gap: 1rem;
          }
        }
      `}</style>
    </section>
  )
}