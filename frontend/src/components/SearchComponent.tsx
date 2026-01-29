/**
 * Search Component
 *
 * Hero-centric search interface with results display and pagination.
 */

import { useState, useEffect, useCallback } from 'react';
import { searchPublications } from '../services/api';
import type { Publication, SearchResponse } from '../types';
import PublicationCard from './PublicationCard';
import './SearchComponent.css';

const PAGE_SIZE_OPTIONS = [10, 20, 50];

export default function SearchComponent() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Publication[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [resultsPerPage, setResultsPerPage] = useState(10);
  const [searchInfo, setSearchInfo] = useState<{
    total: number;
    time: number;
    query: string;
  } | null>(null);

  const totalPages = searchInfo ? Math.max(1, Math.ceil(searchInfo.total / resultsPerPage)) : 0;

  const handleSearch = useCallback(
    async (page: number = 1) => {
      if (!query.trim()) {
        setError('Please enter a search query');
        return;
      }

      setLoading(true);
      setError(null);

      try {
        const response: SearchResponse = await searchPublications(query, page, resultsPerPage);
        setResults(response.results);
        setSearchInfo({
          total: response.total,
          time: response.search_time_ms,
          query: response.query,
        });
        setCurrentPage(page);

        // Scroll to results
        if (page > 1) {
          document.querySelector('.search-results-section')?.scrollIntoView({
            behavior: 'smooth',
            block: 'start',
          });
        }
      } catch (err) {
        console.error('Search error:', err);
        setError('Search failed. Make sure the backend server is running.');
        setResults([]);
      } finally {
        setLoading(false);
      }
    },
    [query, resultsPerPage]
  );

  const handlePageChange = (page: number) => {
    handleSearch(page);
  };

  const clearSearch = () => {
    setQuery('');
    setResults([]);
    setSearchInfo(null);
    setError(null);
    setCurrentPage(1);
  };

  // Keyboard shortcut: Ctrl+K or / to focus search
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey && e.key === 'k') || (e.key === '/' && document.activeElement?.tagName !== 'INPUT')) {
        e.preventDefault();
        document.getElementById('search-input')?.focus();
      }
      if (e.key === 'Enter' && document.activeElement?.id === 'search-input') {
        handleSearch(1);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleSearch]);

  // Generate pagination numbers
  const getPaginationNumbers = () => {
    const pages: (number | 'ellipsis')[] = [];
    const maxVisible = 7;

    if (totalPages <= maxVisible) {
      return Array.from({ length: totalPages }, (_, i) => i + 1);
    }

    // Always show first page
    pages.push(1);

    if (currentPage > 3) {
      pages.push('ellipsis');
    }

    // Show pages around current
    const start = Math.max(2, currentPage - 1);
    const end = Math.min(totalPages - 1, currentPage + 1);

    for (let i = start; i <= end; i++) {
      pages.push(i);
    }

    if (currentPage < totalPages - 2) {
      pages.push('ellipsis');
    }

    // Always show last page
    if (totalPages > 1) {
      pages.push(totalPages);
    }

    return pages;
  };

  return (
    <div className="search-page">
      {/* Hero Section */}
      <section className="search-hero">
        <div className="search-hero-content">
          <h1 className="search-title">
            Discover Academic <span className="search-title-highlight">Research</span>
          </h1>
          <p className="search-subtitle">
            Search through thousands of publications from Coventry University using our
            intelligent TF-IDF powered search engine
          </p>

          <div className="search-box">
            <div className="search-input-wrapper">
              <span className="search-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <circle cx="11" cy="11" r="8" />
                  <path d="M21 21l-4.35-4.35" />
                </svg>
              </span>
              <input
                id="search-input"
                type="text"
                className="search-input"
                placeholder="Search publications, authors, topics..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch(1)}
              />
              {query && (
                <button className="clear-button" onClick={clearSearch} aria-label="Clear search">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <path d="M18 6L6 18M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
            <button className="search-button" onClick={() => handleSearch(1)} disabled={loading}>
              {loading ? 'Searching...' : 'Search'}
            </button>
          </div>

          <p className="search-hint">
            Press <kbd>Ctrl</kbd> + <kbd>K</kbd> to search from anywhere
          </p>
        </div>
      </section>

      {/* Results Section */}
      <section className="search-results-section">
        {error && (
          <div className="error-message">
            <span className="error-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <path d="M12 8v4M12 16h.01" />
              </svg>
            </span>
            {error}
          </div>
        )}

        {searchInfo && !loading && (
          <div className="search-info-bar">
            <p className="search-info">
              Found <strong className="search-info-highlight">{searchInfo.total.toLocaleString()}</strong> results
              for "<strong>{searchInfo.query}</strong>" in{' '}
              <strong>{searchInfo.time.toFixed(2)}ms</strong>
            </p>
            {totalPages > 1 && (
              <p className="search-info">
                Page <strong>{currentPage}</strong> of <strong>{totalPages}</strong>
              </p>
            )}
          </div>
        )}

        {loading && (
          <div className="loading-container">
            <div className="loading-spinner" />
            <p className="loading-text">Searching publications...</p>
          </div>
        )}

        {!loading && results.length > 0 && (
          <>
            <div className="results-container">
              {results.map((pub) => (
                <PublicationCard key={pub.id} publication={pub} />
              ))}
            </div>

            {/* Pagination */}
            {searchInfo && (
              <div className="pagination-wrapper">
                <div className="pagination-header">
                  <p className="pagination-info">
                    Showing <strong>{Math.min(((currentPage - 1) * resultsPerPage) + 1, searchInfo.total)}</strong> - <strong>{Math.min(currentPage * resultsPerPage, searchInfo.total)}</strong> of <strong>{searchInfo.total.toLocaleString()}</strong> results
                  </p>
                  <div className="pagination-size">
                    <label htmlFor="page-size">Per page:</label>
                    <select
                      id="page-size"
                      value={resultsPerPage}
                      onChange={(e) => {
                        setResultsPerPage(Number(e.target.value));
                        setCurrentPage(1);
                      }}
                    >
                      {PAGE_SIZE_OPTIONS.map((size) => (
                        <option key={size} value={size}>
                          {size}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
                <nav className="pagination" aria-label="Search results pagination">
                  {/* First Page */}
                  <button
                    className="pagination-btn pagination-btn--nav"
                    onClick={() => handlePageChange(1)}
                    disabled={currentPage === 1}
                    aria-label="First page"
                    title="First page"
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M11 17l-5-5 5-5M18 17l-5-5 5-5" />
                    </svg>
                  </button>

                  {/* Previous Page */}
                  <button
                    className="pagination-btn pagination-btn--nav"
                    onClick={() => handlePageChange(currentPage - 1)}
                    disabled={currentPage === 1}
                    aria-label="Previous page"
                    title="Previous page"
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M15 18l-6-6 6-6" />
                    </svg>
                  </button>

                  <span className="pagination-divider" />

                  {/* Page Numbers */}
                  {getPaginationNumbers().map((page, index) =>
                    page === 'ellipsis' ? (
                      <span key={`ellipsis-${index}`} className="pagination-ellipsis">
                        •••
                      </span>
                    ) : (
                      <button
                        key={page}
                        className={`pagination-btn ${currentPage === page ? 'active' : ''}`}
                        onClick={() => handlePageChange(page)}
                        aria-label={`Page ${page}`}
                        aria-current={currentPage === page ? 'page' : undefined}
                      >
                        {page}
                      </button>
                    )
                  )}

                  <span className="pagination-divider" />

                  {/* Next Page */}
                  <button
                    className="pagination-btn pagination-btn--nav"
                    onClick={() => handlePageChange(currentPage + 1)}
                    disabled={currentPage === totalPages}
                    aria-label="Next page"
                    title="Next page"
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M9 18l6-6-6-6" />
                    </svg>
                  </button>

                  {/* Last Page */}
                  <button
                    className="pagination-btn pagination-btn--nav"
                    onClick={() => handlePageChange(totalPages)}
                    disabled={currentPage === totalPages}
                    aria-label="Last page"
                    title="Last page"
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M13 17l5-5-5-5M6 17l5-5-5-5" />
                    </svg>
                  </button>
                </nav>
              </div>
            )}
          </>
        )}

        {!loading && searchInfo && results.length === 0 && (
          <div className="no-results">
            <div className="no-results-icon">
              <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <circle cx="11" cy="11" r="8" />
                <path d="M21 21l-4.35-4.35" />
                <path d="M8 8l6 6M14 8l-6 6" />
              </svg>
            </div>
            <h3 className="no-results-title">No publications found</h3>
            <p className="no-results-hint">
              Try different keywords or check your spelling
            </p>
          </div>
        )}

        {/* Initial State - show helpful cards when no search yet */}
        {!searchInfo && !loading && !error && (
          <div className="search-initial-state">
            <div className="initial-state-grid">
              <div className="initial-state-card">
                <div className="initial-state-icon">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                    <path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                  </svg>
                </div>
                <h4 className="initial-state-title">Research Papers</h4>
                <p className="initial-state-desc">Access academic publications and research</p>
              </div>
              <div className="initial-state-card">
                <div className="initial-state-icon">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                    <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" />
                    <circle cx="9" cy="7" r="4" />
                    <path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75" />
                  </svg>
                </div>
                <h4 className="initial-state-title">Author Profiles</h4>
                <p className="initial-state-desc">Find publications by specific researchers</p>
              </div>
              <div className="initial-state-card">
                <div className="initial-state-icon">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                    <path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                </div>
                <h4 className="initial-state-title">Smart Search</h4>
                <p className="initial-state-desc">TF-IDF powered relevance ranking</p>
              </div>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
