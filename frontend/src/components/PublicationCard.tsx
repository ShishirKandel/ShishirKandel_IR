/**
 * Publication Card Component
 *
 * Displays a single publication result with expanded metadata view.
 */

import { useState } from 'react';
import type { Publication } from '../types';
import './PublicationCard.css';

interface PublicationCardProps {
  publication: Publication;
}

export default function PublicationCard({ publication }: PublicationCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const formatDate = (dateString: string | undefined) => {
    if (!dateString) return null;
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
    } catch {
      return dateString;
    }
  };

  const getYear = (dateString: string | undefined) => {
    if (!dateString) return null;
    try {
      return new Date(dateString).getFullYear();
    } catch {
      return null;
    }
  };

  return (
    <article className="publication-card">
      {/* Header with Title and Score */}
      <header className="publication-header">
        <h3 className="publication-title">
          {publication.link ? (
            <a href={publication.link} target="_blank" rel="noopener noreferrer">
              {publication.title}
            </a>
          ) : (
            publication.title
          )}
        </h3>
        {publication.relevance_score !== undefined && (
          <div className="relevance-badge">
            <span className="relevance-icon">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
              </svg>
            </span>
            <span className="relevance-value">{publication.relevance_score.toFixed(3)}</span>
          </div>
        )}
      </header>

      {/* Authors */}
      {publication.authors.length > 0 && (
        <div className="publication-authors">
          {publication.authors.map((author, index) => (
            <span key={author.id} className="author">
              {author.profile_url ? (
                <a href={author.profile_url} target="_blank" rel="noopener noreferrer">
                  {author.name}
                </a>
              ) : (
                author.name
              )}
              {index < publication.authors.length - 1 && (
                <span className="author-separator">,</span>
              )}
            </span>
          ))}
        </div>
      )}

      {/* Abstract */}
      {publication.abstract && (
        <>
          <p className={`publication-abstract ${isExpanded ? 'publication-abstract-expanded' : ''}`}>
            {publication.abstract}
          </p>
          {publication.abstract.length > 200 && (
            <button
              className="expand-button"
              onClick={() => setIsExpanded(!isExpanded)}
            >
              {isExpanded ? 'Show less' : 'Show more'}
              <svg
                width="12"
                height="12"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                style={{ transform: isExpanded ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s ease' }}
              >
                <path d="M6 9l6 6 6-6" />
              </svg>
            </button>
          )}
        </>
      )}

      {/* Tags */}
      <div className="publication-tags">
        {getYear(publication.published_date) && (
          <span className="publication-tag">
            <svg className="publication-tag-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
              <line x1="16" y1="2" x2="16" y2="6" />
              <line x1="8" y1="2" x2="8" y2="6" />
              <line x1="3" y1="10" x2="21" y2="10" />
            </svg>
            {getYear(publication.published_date)}
          </span>
        )}
        {publication.authors.length > 0 && (
          <span className="publication-tag">
            <svg className="publication-tag-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" />
              <circle cx="9" cy="7" r="4" />
            </svg>
            {publication.authors.length} author{publication.authors.length !== 1 ? 's' : ''}
          </span>
        )}
        <span className="publication-tag">
          <svg className="publication-tag-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
            <polyline points="14 2 14 8 20 8" />
          </svg>
          Research Paper
        </span>
      </div>

      {/* Footer */}
      <footer className="publication-footer">
        <div className="publication-meta">
          {publication.published_date && (
            <span className="meta-item">
              <span className="meta-item-icon">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                  <polyline points="12 6 12 12 16 14" />
                </svg>
              </span>
              {formatDate(publication.published_date)}
            </span>
          )}
          {publication.id && (
            <span className="meta-item">
              <span className="meta-item-icon">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
                  <polyline points="22,6 12,13 2,6" />
                </svg>
              </span>
              ID: {publication.id}
            </span>
          )}
        </div>

        <div className="publication-actions">
          {publication.link && (
            <a
              href={publication.link}
              target="_blank"
              rel="noopener noreferrer"
              className="publication-link"
            >
              View Publication
              <span className="publication-link-icon">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6" />
                  <polyline points="15 3 21 3 21 9" />
                  <line x1="10" y1="14" x2="21" y2="3" />
                </svg>
              </span>
            </a>
          )}
        </div>
      </footer>
    </article>
  );
}
