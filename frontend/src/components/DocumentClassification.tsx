/**
 * Document Classification Component
 *
 * Interface for classifying text using Naive Bayes or Logistic Regression.
 */

import { useState } from 'react';
import { classifyText, getModelInfo } from '../services/api';
import type { ClassificationResult, ModelInfo } from '../types';
import './DocumentClassification.css';

/**
 * ROBUSTNESS SAMPLES - Designed for Viva Demonstration
 * 
 * These samples demonstrate classification robustness across:
 * 1. Short inputs (with and without stopwords)
 * 2. Medium inputs (standard sentences)
 * 3. Long inputs (full paragraphs)
 * 4. Edge cases (challenging/mixed vocabulary)
 * 
 * All vocabulary is derived from training_documents.csv patterns.
 */
type SampleType = 'short_keywords' | 'short_natural' | 'medium' | 'long' | 'edge_case' | 'edge_case_2';

interface SampleText {
  label: string;
  text: string;
  description: string;
}

const ROBUSTNESS_SAMPLES: Record<string, Record<SampleType, SampleText>> = {
  business: {
    short_keywords: {
      label: "Short (Keywords Only)",
      text: "wall street stock investors earnings corporate profits",
      description: "No stopwords, pure business keywords"
    },
    short_natural: {
      label: "Short (Natural)",
      text: "Wall Street stocks surged as investors reacted to the Federal Reserve interest rate decision.",
      description: "With stopwords, natural sentence"
    },
    medium: {
      label: "Medium",
      text: "The CEO announced quarterly earnings that exceeded analyst expectations, driving the company stock price to record highs. Corporate profits continue to grow amid strong consumer spending and the startup ecosystem attracts venture capital investors.",
      description: "Two sentences, multiple business themes"
    },
    long: {
      label: "Long Paragraph",
      text: "Major banks are facing increased regulatory scrutiny after the latest financial crisis. Wall Street executives defend their bonus structures while Congress debates new tax reforms that could affect corporate profits. The startup ecosystem continues to attract venture capital investors despite economic uncertainty, with entrepreneurs seeking funding for innovative technology solutions. Meanwhile, the Federal Reserve is monitoring inflation and may adjust interest rates to stimulate economic growth. Corporate mergers and acquisitions have reached record levels as companies seek to expand market share and improve shareholder returns.",
      description: "Full paragraph with diverse business vocabulary"
    },
    edge_case: {
      label: "Challenging 1",
      text: "The entertainment industry CEO announced record profits from streaming services. The company stock price reflects strong investor confidence in the corporate media strategy.",
      description: "Media business - overlaps entertainment"
    },
    edge_case_2: {
      label: "Challenging 2",
      text: "Healthcare startup raises millions from venture capital investors. The pharmaceutical company IPO exceeded Wall Street expectations and analysts predict strong corporate earnings growth.",
      description: "Healthcare business - overlaps health"
    }
  },
  entertainment: {
    short_keywords: {
      label: "Short (Keywords Only)",
      text: "oscar film actor hollywood movie premiere grammy",
      description: "No stopwords, pure entertainment keywords"
    },
    short_natural: {
      label: "Short (Natural)",
      text: "The Oscar-nominated film premiered at the Sundance Film Festival to rave reviews from critics.",
      description: "With stopwords, natural sentence"
    },
    medium: {
      label: "Medium",
      text: "Netflix announced a new original series starring Emmy-winning actors, joining a growing lineup of streaming content. The blockbuster movie dominated the weekend box office with record-breaking ticket sales and critics praised the director vision.",
      description: "Two sentences, multiple entertainment themes"
    },
    long: {
      label: "Long Paragraph",
      text: "Grammy-winning singer Taylor Swift released her highly anticipated album, breaking streaming records on Spotify. Meanwhile, Marvel Studios announced several new superhero films starring popular Hollywood actors. The Broadway musical received standing ovations from theater audiences and critics praised the director creative vision and the stellar cast performances. The Academy Awards ceremony honored films that tackled important social issues, and Netflix continues to dominate the streaming wars with original content attracting millions of viewers worldwide.",
      description: "Full paragraph with diverse entertainment vocabulary"
    },
    edge_case: {
      label: "Challenging 1",
      text: "The Oscar-winning actor revealed his struggle during an interview on the Netflix documentary premiere. The film director shared how the intense movie shoot affected the entire Hollywood cast.",
      description: "Personal struggles - slight personal overlap"
    },
    edge_case_2: {
      label: "Challenging 2",
      text: "The blockbuster movie about Wall Street traders starring Oscar-winning actors premieres this weekend. Netflix acquired streaming rights and critics praise the film portrayal of corporate executives.",
      description: "Business-themed movie - overlaps business"
    }
  },
  health: {
    short_keywords: {
      label: "Short (Keywords Only)",
      text: "doctor patient cancer treatment hospital clinical trial",
      description: "No stopwords, pure health keywords"
    },
    short_natural: {
      label: "Short (Natural)",
      text: "Doctors recommend regular exercise and proper sleep to reduce risk of heart disease and diabetes.",
      description: "With stopwords, natural sentence"
    },
    medium: {
      label: "Medium",
      text: "Clinical trials for the new cancer treatment showed promising results, with patients experiencing fewer side effects compared to traditional chemotherapy. Researchers continue to study the relationship between diet and chronic disease prevention.",
      description: "Two sentences, multiple health themes"
    },
    long: {
      label: "Long Paragraph",
      text: "Medical researchers discovered a breakthrough therapy for treating depression and anxiety disorders. The FDA approved a new drug for patients suffering from rheumatoid arthritis after successful clinical trials. Hospitals are implementing new protocols to improve patient outcomes, while physicians emphasize the importance of preventive care including regular screenings and healthy lifestyle choices. New studies show that sleep disorders can increase risk of heart disease and diabetes, and doctors recommend lifestyle changes before prescribing medications.",
      description: "Full paragraph with diverse health vocabulary"
    },
    edge_case: {
      label: "Challenging 1",
      text: "The pharmaceutical company reported strong earnings after FDA approval of their new drug. Investors are optimistic about the corporate profits from cancer treatment medications.",
      description: "Pharma business - overlaps business"
    },
    edge_case_2: {
      label: "Challenging 2",
      text: "The documentary film follows patients through their cancer treatment journey at the hospital. Doctors share medical insights while the director captures emotional moments between physicians and families.",
      description: "Medical documentary - overlaps entertainment"
    }
  }
};

// Legacy fallback for simple access
const SAMPLE_TEXTS = {
  business: {
    short: ROBUSTNESS_SAMPLES.business.short_natural.text,
    medium: ROBUSTNESS_SAMPLES.business.medium.text,
    long: ROBUSTNESS_SAMPLES.business.long.text
  },
  entertainment: {
    short: ROBUSTNESS_SAMPLES.entertainment.short_natural.text,
    medium: ROBUSTNESS_SAMPLES.entertainment.medium.text,
    long: ROBUSTNESS_SAMPLES.entertainment.long.text
  },
  health: {
    short: ROBUSTNESS_SAMPLES.health.short_natural.text,
    medium: ROBUSTNESS_SAMPLES.health.medium.text,
    long: ROBUSTNESS_SAMPLES.health.long.text
  }
};



export default function DocumentClassification() {
  const [text, setText] = useState('');
  const [modelType, setModelType] = useState<'naive_bayes' | 'logistic_regression'>(
    'naive_bayes'
  );
  const [result, setResult] = useState<ClassificationResult | null>(null);
  const [modelInfo, setModelInfo] = useState<ModelInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleClassify = async () => {
    if (!text.trim()) {
      setError('Please enter text to classify');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await classifyText(text, modelType);
      setResult(response);
    } catch (err) {
      console.error('Classification error:', err);
      setError('Classification failed. Make sure the backend is running and models are trained.');
    } finally {
      setLoading(false);
    }
  };

  const [sampleLength, setSampleLength] = useState<'short' | 'medium' | 'long'>('medium');
  const [robustnessMode, setRobustnessMode] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<'business' | 'entertainment' | 'health'>('business');
  const [sampleType, setSampleType] = useState<SampleType>('medium');

  const loadSampleText = (category: 'business' | 'entertainment' | 'health') => {
    setText(SAMPLE_TEXTS[category][sampleLength]);
    setResult(null);
  };

  const loadRobustnessSample = (category: 'business' | 'entertainment' | 'health', type: SampleType) => {
    setSelectedCategory(category);
    setSampleType(type);
    setText(ROBUSTNESS_SAMPLES[category][type].text);
    setResult(null);
  };

  const loadModelInfo = async () => {
    try {
      const info = await getModelInfo();
      setModelInfo(info);
    } catch (err) {
      console.error('Failed to load model info:', err);
    }
  };

  return (
    <div className="classification-page">
      {/* Header */}
      <header className="classification-header">
        <h1 className="classification-title">Document Classification</h1>
        <p className="classification-subtitle">
          Classify text into Business, Entertainment, or Health categories using machine learning models
        </p>
      </header>

      <div className="classification-container">
        {/* Model Selector */}
        <div className="model-selector">
          <label className="model-option">
            <input
              type="radio"
              name="model"
              value="naive_bayes"
              checked={modelType === 'naive_bayes'}
              onChange={() => setModelType('naive_bayes')}
            />
            <span className="model-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
              </svg>
            </span>
            <span className="model-label">
              <strong>Naive Bayes</strong>
              <small>Probabilistic classifier</small>
            </span>
          </label>

          <label className="model-option">
            <input
              type="radio"
              name="model"
              value="logistic_regression"
              checked={modelType === 'logistic_regression'}
              onChange={() => setModelType('logistic_regression')}
            />
            <span className="model-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
                <line x1="18" y1="20" x2="18" y2="10" />
                <line x1="12" y1="20" x2="12" y2="4" />
                <line x1="6" y1="20" x2="6" y2="14" />
              </svg>
            </span>
            <span className="model-label">
              <strong>Logistic Regression</strong>
              <small>Linear classifier</small>
            </span>
          </label>

          <button className="info-button" onClick={loadModelInfo}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <path d="M12 16v-4M12 8h.01" />
            </svg>
            Model Info
          </button>
        </div>

        {/* Sample Texts */}
        <div className="sample-texts">
          <div className="sample-header">
            <span className="sample-label">Try a sample:</span>
            <label className="robustness-toggle">
              <input
                type="checkbox"
                checked={robustnessMode}
                onChange={(e) => setRobustnessMode(e.target.checked)}
              />
              <span className="toggle-slider"></span>
              <span className="toggle-label">Robustness Test Mode</span>
            </label>
          </div>

          {!robustnessMode ? (
            /* Standard Mode */
            <>
              <div className="sample-buttons">
                <button className="sample-btn business" onClick={() => loadSampleText('business')}>
                  Business
                </button>
                <button className="sample-btn entertainment" onClick={() => loadSampleText('entertainment')}>
                  Entertainment
                </button>
                <button className="sample-btn health" onClick={() => loadSampleText('health')}>
                  Health
                </button>
              </div>
              <div className="sample-length-selector">
                <span>Length:</span>
                <select value={sampleLength} onChange={(e) => setSampleLength(e.target.value as 'short' | 'medium' | 'long')}>
                  <option value="short">Short</option>
                  <option value="medium">Medium</option>
                  <option value="long">Long</option>
                </select>
              </div>
            </>
          ) : (
            /* Robustness Test Mode */
            <div className="robustness-panel">
              <p className="robustness-description">
                Test classification accuracy across different input types and lengths
              </p>

              {/* Category Selector */}
              <div className="robustness-category-selector">
                <button
                  className={`category-tab ${selectedCategory === 'business' ? 'active business' : ''}`}
                  onClick={() => setSelectedCategory('business')}
                >
                  Business
                </button>
                <button
                  className={`category-tab ${selectedCategory === 'entertainment' ? 'active entertainment' : ''}`}
                  onClick={() => setSelectedCategory('entertainment')}
                >
                  Entertainment
                </button>
                <button
                  className={`category-tab ${selectedCategory === 'health' ? 'active health' : ''}`}
                  onClick={() => setSelectedCategory('health')}
                >
                  Health
                </button>
              </div>

              {/* Sample Type Grid */}
              <div className="robustness-samples-grid">
                {(Object.keys(ROBUSTNESS_SAMPLES[selectedCategory]) as SampleType[]).map((type) => {
                  const sample = ROBUSTNESS_SAMPLES[selectedCategory][type];
                  return (
                    <button
                      key={type}
                      className={`robustness-sample-btn ${sampleType === type ? 'active' : ''} ${type === 'edge_case' ? 'edge-case' : ''}`}
                      onClick={() => loadRobustnessSample(selectedCategory, type)}
                    >
                      <span className="sample-type-label">{sample.label}</span>
                      <span className="sample-type-desc">{sample.description}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Input Section */}
        <div className="input-section">
          <textarea
            className="text-input"
            placeholder="Enter or paste text to classify..."
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={6}
          />
          <div className="input-actions">
            <span className="char-count">{text.length} characters</span>
            <button className="classify-button" onClick={handleClassify} disabled={loading}>
              {loading ? (
                <>
                  <svg className="animate-spin" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 12a9 9 0 11-6.219-8.56" />
                  </svg>
                  Classifying...
                </>
              ) : (
                <>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M22 11.08V12a10 10 0 11-5.93-9.14" />
                    <polyline points="22 4 12 14.01 9 11.01" />
                  </svg>
                  Classify Text
                </>
              )}
            </button>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="error-message">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <path d="M12 8v4M12 16h.01" />
            </svg>
            {error}
          </div>
        )}

        {/* Result Section */}
        {result && (
          <div className="result-section">
            <div className={`result-category ${result.category.toLowerCase()}`}>
              <div className="category-label">Predicted Category</div>
              <div className="category-value">{result.category}</div>
              <div className="confidence-value">{(result.confidence * 100).toFixed(1)}% confidence</div>
            </div>

            <div className="probabilities">
              <h4>Category Probabilities</h4>
              {Object.entries(result.probabilities).map(([category, prob]) => (
                <div key={category} className="probability-bar">
                  <span className="probability-label">{category}</span>
                  <div className="probability-track">
                    <div
                      className={`probability-fill ${category.toLowerCase()}`}
                      style={{ width: `${prob * 100}%` }}
                    />
                  </div>
                  <span className="probability-value">{(prob * 100).toFixed(1)}%</span>
                </div>
              ))}
            </div>

            {result.explanation && (
              <div className="result-explanation">
                <h4>Analysis</h4>
                <p>{result.explanation}</p>
              </div>
            )}

            <div className="result-meta">
              <span>Model: {result.model_used}</span>
              {result.preprocessing_info && (
                <span>
                  Tokens: {result.preprocessing_info.processed_token_count} (from{' '}
                  {result.preprocessing_info.original_word_count} words)
                </span>
              )}
            </div>
          </div>
        )}

        {/* Model Info Modal */}
        {modelInfo && (
          <>
            <div className="model-info-backdrop" onClick={() => setModelInfo(null)} />
            <div className="model-info-panel">
              <h4>Model Information</h4>
              <p>
                Training documents: <strong>{modelInfo.training_documents_count}</strong>
              </p>
              <p>
                Categories: <strong>{modelInfo.categories.join(', ')}</strong>
              </p>
              {modelInfo.models.naive_bayes && (
                <p>
                  Naive Bayes:{' '}
                  <strong>
                    {modelInfo.models.naive_bayes.is_trained ? 'Trained' : 'Not trained'}
                    {modelInfo.models.naive_bayes.accuracy &&
                      ` (${(modelInfo.models.naive_bayes.accuracy * 100).toFixed(1)}% accuracy)`}
                  </strong>
                </p>
              )}
              {modelInfo.models.logistic_regression && (
                <p>
                  Logistic Regression:{' '}
                  <strong>
                    {modelInfo.models.logistic_regression.is_trained ? 'Trained' : 'Not trained'}
                    {modelInfo.models.logistic_regression.accuracy &&
                      ` (${(modelInfo.models.logistic_regression.accuracy * 100).toFixed(1)}% accuracy)`}
                  </strong>
                </p>
              )}
              <button className="model-info-close" onClick={() => setModelInfo(null)}>
                Close
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
