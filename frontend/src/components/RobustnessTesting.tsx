/**
 * Robustness Testing Component
 *
 * Tests classification with various input types and edge cases.
 */

import { useState } from 'react';
import { batchClassify, type BatchClassifyResult } from '../services/api';
import './RobustnessTesting.css';

interface TestCase {
  input: string;
  expected: string;
  category: string;
}

const TEST_CASES: Record<string, TestCase[]> = {
  'Short Keywords': [
    { input: 'stock market', expected: 'business', category: 'short' },
    { input: 'wall street investors', expected: 'business', category: 'short' },
    { input: 'corporate profits', expected: 'business', category: 'short' },
    { input: 'movie premiere', expected: 'entertainment', category: 'short' },
    { input: 'oscar film actor', expected: 'entertainment', category: 'short' },
    { input: 'grammy award singer', expected: 'entertainment', category: 'short' },
    { input: 'diabetes treatment', expected: 'health', category: 'short' },
    { input: 'doctor patient hospital', expected: 'health', category: 'short' },
    { input: 'cancer clinical trial', expected: 'health', category: 'short' },
  ],
  'Natural Sentences': [
    { input: 'The CEO announced strong quarterly earnings.', expected: 'business', category: 'natural' },
    { input: 'Wall Street stocks surged on the investor news.', expected: 'business', category: 'natural' },
    { input: 'The startup raised venture capital funding.', expected: 'business', category: 'natural' },
    { input: 'The Oscar-nominated film premiered to rave reviews.', expected: 'entertainment', category: 'natural' },
    { input: 'Netflix released a new original series.', expected: 'entertainment', category: 'natural' },
    { input: 'The Grammy-winning singer released her album.', expected: 'entertainment', category: 'natural' },
    { input: 'Doctors recommend regular exercise for health.', expected: 'health', category: 'natural' },
    { input: 'The FDA approved a new cancer treatment drug.', expected: 'health', category: 'natural' },
    { input: 'Patients experienced fewer side effects with therapy.', expected: 'health', category: 'natural' },
  ],
  'Long Paragraphs': [
    {
      input: `The quarterly earnings report shows a significant increase in revenue. The company's stock price 
      surged after the announcement of the merger. Wall Street analysts predict strong growth in the upcoming 
      fiscal year with improved profit margins and market expansion strategies. Corporate executives are 
      optimistic about shareholder returns.`,
      expected: 'business',
      category: 'long',
    },
    {
      input: `The new blockbuster movie premiered at the film festival to rave reviews. The celebrity cast 
      attended the red carpet event, and critics praised the director's innovative storytelling. The 
      soundtrack features collaborations with Grammy-winning artists. Netflix acquired streaming rights 
      for the Oscar-nominated production.`,
      expected: 'entertainment',
      category: 'long',
    },
    {
      input: `Recent medical research has shown promising results for the new cancer treatment. Clinical 
      trials indicate improved patient outcomes with fewer side effects. The FDA is expected to review 
      the drug application next month following positive Phase 3 results. Doctors are optimistic about 
      therapy options for patients suffering from chronic diseases.`,
      expected: 'health',
      category: 'long',
    },
  ],
  'Stopword-Heavy': [
    { input: 'the company is doing very well in the stock market this year', expected: 'business', category: 'stopword' },
    { input: 'the investors are very happy with the earnings report', expected: 'business', category: 'stopword' },
    { input: 'the movie was really good and the actors did a great job', expected: 'entertainment', category: 'stopword' },
    { input: 'the film is getting a lot of attention from critics', expected: 'entertainment', category: 'stopword' },
    { input: 'the patient is doing well after the treatment at hospital', expected: 'health', category: 'stopword' },
    { input: 'the doctor said that the therapy is working for them', expected: 'health', category: 'stopword' },
  ],
  'Challenging Mixed': [
    { input: 'Healthcare company stock rises after FDA approval', expected: 'health', category: 'mixed' },
    { input: 'Celebrity invests millions in tech startup venture', expected: 'business', category: 'mixed' },
    { input: 'Pharmaceutical earnings exceed Wall Street expectations', expected: 'business', category: 'mixed' },
    { input: 'Oscar-winning actor opens new restaurant business', expected: 'entertainment', category: 'mixed' },
    { input: 'Netflix documentary about hospital patients premieres', expected: 'entertainment', category: 'mixed' },
    { input: 'Hollywood star discusses mental wellness journey', expected: 'entertainment', category: 'mixed' },
    { input: 'Sports athlete recovers from surgery with new therapy', expected: 'health', category: 'mixed' },
    { input: 'Medical documentary wins award at film festival', expected: 'entertainment', category: 'mixed' },
  ],
  'Edge Cases': [
    { input: '', expected: 'empty', category: 'edge' },
    { input: '!@#$%^&*()', expected: 'special', category: 'edge' },
    { input: '123456789', expected: 'numbers', category: 'edge' },
    { input: 'a', expected: 'single', category: 'edge' },
    { input: 'https://example.com', expected: 'url', category: 'edge' },
    { input: '   ', expected: 'whitespace', category: 'edge' },
  ],
};

export default function RobustnessTesting() {
  const [results, setResults] = useState<BatchClassifyResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  const runTests = async () => {
    setLoading(true);
    setError(null);

    try {
      const allTexts = Object.values(TEST_CASES)
        .flat()
        .map((tc) => tc.input);

      const result = await batchClassify(allTexts, 'naive_bayes');
      setResults(result);
    } catch (err) {
      console.error('Test failed:', err);
      setError('Failed to run tests. Make sure models are trained.');
    } finally {
      setLoading(false);
    }
  };

  const getExpectedForInput = (input: string): string => {
    for (const tests of Object.values(TEST_CASES)) {
      const found = tests.find((t) => t.input === input);
      if (found) return found.expected;
    }
    return 'unknown';
  };

  const getCategoryForInput = (input: string): string => {
    for (const tests of Object.values(TEST_CASES)) {
      const found = tests.find((t) => t.input === input);
      if (found) return found.category;
    }
    return 'unknown';
  };

  const isCorrect = (result: string, expected: string): boolean => {
    // Edge cases that are expected to return 'unknown' or any result
    if (['unknown', 'empty', 'special', 'numbers', 'single', 'url', 'whitespace'].includes(expected)) {
      return true;
    }
    return result.toLowerCase() === expected.toLowerCase();
  };

  const filteredResults =
    results?.results.filter((r) => {
      if (selectedCategory === 'all') return true;
      return getCategoryForInput(r.input) === selectedCategory;
    }) || [];

  const stats = results
    ? {
      total: results.results.length,
      nbCorrect: results.results.filter((r) =>
        isCorrect(r.naive_bayes?.category || '', getExpectedForInput(r.input))
      ).length,
    }
    : null;

  return (
    <div className="robustness-page">
      {/* Header */}
      <header className="robustness-header">
        <h1 className="robustness-title">
          <span className="robustness-title-icon">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14.7 6.3a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l3.77-3.77a6 6 0 01-7.94 7.94l-6.91 6.91a2.12 2.12 0 01-3-3l6.91-6.91a6 6 0 017.94-7.94l-3.76 3.76z" />
            </svg>
          </span>
          Robustness Testing
        </h1>
        <p className="robustness-subtitle">
          Test classification models across various input types and edge cases
        </p>
      </header>

      <div className="robustness-container">
        {/* Controls */}
        <div className="test-controls">
          <button onClick={runTests} disabled={loading} className="run-tests-btn">
            {loading ? (
              <>
                <svg className="animate-spin" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 12a9 9 0 11-6.219-8.56" />
                </svg>
                Running Tests...
              </>
            ) : (
              <>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polygon points="5 3 19 12 5 21 5 3" />
                </svg>
                Run All Tests
              </>
            )}
          </button>

          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="category-select"
          >
            <option value="all">All Tests</option>
            <option value="short">Short Keywords</option>
            <option value="natural">Natural Sentences</option>
            <option value="long">Long Paragraphs</option>
            <option value="stopword">Stopword-Heavy</option>
            <option value="mixed">Challenging Mixed</option>
            <option value="edge">Edge Cases</option>
          </select>
        </div>

        {/* Error */}
        {error && (
          <div className="error-message">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <path d="M12 8v4M12 16h.01" />
            </svg>
            {error}
          </div>
        )}

        {/* Stats Summary */}
        {stats && (
          <div className="stats-summary">
            <div className="stat-box">
              <span className="stat-label">Total Tests</span>
              <span className="stat-value">{stats.total}</span>
            </div>
            <div className="stat-box nb">
              <span className="stat-label">Naive Bayes</span>
              <span className="stat-value">
                {stats.nbCorrect}/{stats.total} ({((stats.nbCorrect / stats.total) * 100).toFixed(0)}%)
              </span>
            </div>
          </div>
        )}

        {/* Results Table */}
        {results && (
          <div className="results-table-container">
            <table className="results-table">
              <thead>
                <tr>
                  <th>Input</th>
                  <th>Expected</th>
                  <th>Naive Bayes</th>
                </tr>
              </thead>
              <tbody>
                {filteredResults.map((result, idx) => {
                  const expected = getExpectedForInput(result.input);
                  const nbCorrect = isCorrect(result.naive_bayes?.category || '', expected);

                  return (
                    <tr key={idx}>
                      <td className={`input-cell ${!result.input ? 'empty' : ''}`} title={result.input}>
                        {result.input.length > 50 ? result.input.substring(0, 50) + '...' : result.input || '(empty)'}
                      </td>
                      <td className="expected-cell">{expected}</td>
                      <td className={`result-cell ${nbCorrect ? 'correct' : 'incorrect'}`}>
                        {result.naive_bayes?.category || 'error'}
                        <span className="confidence">
                          ({((result.naive_bayes?.confidence || 0) * 100).toFixed(0)}%)
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Initial State - Test Categories */}
        {!results && !loading && (
          <div className="test-categories">
            <h2 className="test-categories-title">Test Categories</h2>
            <div className="categories-grid">
              {Object.entries(TEST_CASES).map(([category, tests]) => (
                <div key={category} className="category-card">
                  <div className="category-card-header">
                    <h3>{category}</h3>
                    <span className="category-count">{tests.length} tests</span>
                  </div>
                  <ul>
                    {tests.slice(0, 3).map((t, i) => (
                      <li key={i}>{t.input.substring(0, 40) || '(empty)'}...</li>
                    ))}
                    {tests.length > 3 && <li className="more">...and {tests.length - 3} more</li>}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
