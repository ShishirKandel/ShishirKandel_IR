/**
 * API Service for the IR Search Engine
 * 
 * Provides functions to interact with the Django REST API.
 */

import axios from 'axios';
import type {
    SearchResponse,
    ClassificationResult,
    ModelInfo,
    CrawlerStatus,
    IndexStats,
    ApiInfo
} from '../types';

// API base URL - Django backend
const API_BASE_URL = 'http://localhost:8000/api';

// Create axios instance with default config
const api = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json',
    },
});

/**
 * Get API information
 */
export async function getApiInfo(): Promise<ApiInfo> {
    const response = await api.get<ApiInfo>('/');
    return response.data;
}

/**
 * Search publications
 */
export async function searchPublications(
    query: string,
    page: number = 1,
    size: number = 10
): Promise<SearchResponse> {
    const response = await api.get<SearchResponse>('/search/', {
        params: { query, page, size },
    });
    return response.data;
}

/**
 * Classify text using Naive Bayes or Logistic Regression
 */
export async function classifyText(
    text: string,
    modelType: 'naive_bayes' | 'logistic_regression' = 'naive_bayes'
): Promise<ClassificationResult> {
    const response = await api.post<ClassificationResult>('/classify/', {
        text,
        model_type: modelType,
    });
    return response.data;
}

/**
 * Get model information
 */
export async function getModelInfo(modelType?: string): Promise<ModelInfo> {
    const response = await api.get<ModelInfo>('/model-info/', {
        params: modelType ? { model_type: modelType } : {},
    });
    return response.data;
}

/**
 * Get crawler status
 */
export async function getCrawlerStatus(): Promise<CrawlerStatus> {
    const response = await api.get<CrawlerStatus>('/crawler-status/');
    return response.data;
}

/**
 * Trigger manual crawl
 */
export async function triggerCrawl(): Promise<{ message: string; task_id: string }> {
    const response = await api.post('/trigger-crawl/');
    return response.data;
}

/**
 * Get index statistics
 */
export async function getIndexStats(): Promise<IndexStats> {
    const response = await api.get<IndexStats>('/index-stats/');
    return response.data;
}

/**
 * Get sample inverted index entries
 */
export async function getIndexInfo(sampleSize: number = 50): Promise<{
    sample_size: number;
    entries: Array<{
        term: string;
        publication_title: string;
        tfidf_score: number;
        term_frequency: number;
    }>;
}> {
    const response = await api.get('/index-info/', {
        params: { sample_size: sampleSize },
    });
    return response.data;
}

/**
 * Batch classify multiple texts for robustness testing
 */
export interface BatchClassifyResult {
    total: number;
    results: Array<{
        input: string;
        naive_bayes?: { category: string; confidence: number; error?: string };
    }>;
}

export async function batchClassify(
    texts: string[],
    modelType: 'naive_bayes' = 'naive_bayes'
): Promise<BatchClassifyResult> {
    const response = await api.post<BatchClassifyResult>('/batch-classify/', {
        texts,
        model_type: modelType,
    });
    return response.data;
}

export default api;
