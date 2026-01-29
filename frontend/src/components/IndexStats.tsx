/**
 * Index Stats Component
 *
 * Displays inverted index statistics and crawler status.
 */

import { useState, useEffect } from 'react';
import { getIndexStats, getCrawlerStatus } from '../services/api';
import type { IndexStats, CrawlerStatus } from '../types';
import './IndexStats.css';

export default function IndexStatsComponent() {
  const [stats, setStats] = useState<IndexStats | null>(null);
  const [crawlerStatus, setCrawlerStatus] = useState<CrawlerStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [statsData, crawlerData] = await Promise.all([getIndexStats(), getCrawlerStatus()]);
      setStats(statsData);
      setCrawlerStatus(crawlerData);
    } catch (err) {
      console.error('Failed to load stats:', err);
      setError('Failed to load statistics. Make sure the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num: number) => {
    return num.toLocaleString();
  };

  if (loading) {
    return (
      <div className="stats-page">
        <div className="loading-container">
          <div className="loading-spinner" />
          <p className="loading-text">Loading statistics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="stats-page">
        <div className="error-container">
          <div className="error-message">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <path d="M12 8v4M12 16h.01" />
            </svg>
            {error}
          </div>
          <button onClick={loadData} className="retry-button">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M23 4v6h-6M1 20v-6h6" />
              <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15" />
            </svg>
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="stats-page">
      {/* Header */}
      <header className="stats-header">
        <h1 className="stats-title">Index Statistics</h1>
        <p className="stats-subtitle">
          Monitor your search engine's inverted index and crawler performance
        </p>
      </header>

      <div className="stats-container">
        {/* Stats Grid */}
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
                <polyline points="14 2 14 8 20 8" />
                <line x1="16" y1="13" x2="8" y2="13" />
                <line x1="16" y1="17" x2="8" y2="17" />
                <polyline points="10 9 9 9 8 9" />
              </svg>
            </div>
            <span className="stat-value">{formatNumber(stats?.total_documents || 0)}</span>
            <span className="stat-label">Total Documents</span>
          </div>

          <div className="stat-card">
            <div className="stat-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M4 7V4h16v3M9 20h6M12 4v16" />
              </svg>
            </div>
            <span className="stat-value">{formatNumber(stats?.unique_terms || 0)}</span>
            <span className="stat-label">Unique Terms</span>
          </div>

          <div className="stat-card">
            <div className="stat-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="20" x2="18" y2="10" />
                <line x1="12" y1="20" x2="12" y2="4" />
                <line x1="6" y1="20" x2="6" y2="14" />
              </svg>
            </div>
            <span className="stat-value">{formatNumber(stats?.total_terms || 0)}</span>
            <span className="stat-label">Index Entries</span>
          </div>

          <div className="stat-card">
            <div className="stat-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
              </svg>
            </div>
            <span className="stat-value">{stats?.avg_document_length?.toFixed(1) || '0'}</span>
            <span className="stat-label">Avg. Doc Length</span>
          </div>
        </div>

        {/* Crawler Section */}
        {crawlerStatus && (
          <div className="crawler-section">
            <div className="crawler-header">
              <h2>
                <span className="crawler-header-icon">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
                  </svg>
                </span>
                Crawler Status
              </h2>
              <span className={`status-badge ${crawlerStatus.is_running ? 'running' : 'idle'}`}>
                <span className="status-indicator" />
                {crawlerStatus.is_running ? 'Running' : 'Idle'}
              </span>
            </div>

            <div className="crawler-info">
              <div className="crawler-detail">
                <span className="detail-label">
                  <svg className="detail-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M23 4v6h-6M1 20v-6h6" />
                    <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15" />
                  </svg>
                  Total Crawls
                </span>
                <span className="detail-value">{formatNumber(crawlerStatus.total_crawls)}</span>
              </div>

              <div className="crawler-detail">
                <span className="detail-label">
                  <svg className="detail-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                  </svg>
                  Total Publications
                </span>
                <span className="detail-value">{formatNumber(crawlerStatus.total_publications)}</span>
              </div>

              <div className="crawler-detail">
                <span className="detail-label">
                  <svg className="detail-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10" />
                    <polyline points="12 6 12 12 16 14" />
                  </svg>
                  Schedule
                </span>
                <span className="detail-value">{crawlerStatus.schedule_info}</span>
              </div>

              {crawlerStatus.last_crawl && (
                <div className="crawler-detail">
                  <span className="detail-label">
                    <svg className="detail-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
                      <line x1="16" y1="2" x2="16" y2="6" />
                      <line x1="8" y1="2" x2="8" y2="6" />
                      <line x1="3" y1="10" x2="21" y2="10" />
                    </svg>
                    Last Crawl
                  </span>
                  <span className="detail-value">
                    {new Date(crawlerStatus.last_crawl.crawl_time).toLocaleString()}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Refresh Button */}
        <div className="stats-actions">
          <button onClick={loadData} className="refresh-button">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M23 4v6h-6M1 20v-6h6" />
              <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15" />
            </svg>
            Refresh Stats
          </button>
        </div>
      </div>
    </div>
  );
}
