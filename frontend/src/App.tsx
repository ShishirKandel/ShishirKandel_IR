/**
 * IR Search Engine - Main Application
 *
 * ST7071CEM - Intelligent Information Retrieval Assignment
 * Coventry University / Softwarica College
 */

import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import SearchComponent from './components/SearchComponent';
import DocumentClassification from './components/DocumentClassification';
import IndexStats from './components/IndexStats';
import RobustnessTesting from './components/RobustnessTesting';
import './App.css';

function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <Header />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<SearchComponent />} />
            <Route path="/classify" element={<DocumentClassification />} />
            <Route path="/stats" element={<IndexStats />} />
            <Route path="/robustness" element={<RobustnessTesting />} />
          </Routes>
        </main>
        <footer className="footer">
          <div className="footer-content">
            <div className="footer-brand">
              <span className="footer-logo">S</span>
              <span className="footer-title">ScholarSearch</span>
            </div>
            <p className="footer-text">
              Intelligent Information Retrieval Search Engine
              <br />
              ST7071CEM Assignment &bull;{' '}
              <a
                href="https://pureportal.coventry.ac.uk"
                target="_blank"
                rel="noopener noreferrer"
                className="footer-link"
              >
                Coventry University Publications
              </a>
            </p>
            <div className="footer-divider" />
            <p className="footer-meta">
              Built with React, TypeScript & TF-IDF
            </p>
          </div>
        </footer>
      </div>
    </BrowserRouter>
  );
}

export default App;
