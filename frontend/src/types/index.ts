/**
 * TypeScript interfaces for the IR Search Engine
 */

export interface Author {
    id: number;
    name: string;
    profile_url: string | null;
}

export interface Publication {
    id: number;
    title: string;
    link: string;
    abstract: string;
    published_date: string;
    authors: Author[];
    relevance_score?: number;
}

export interface SearchResponse {
    results: Publication[];
    total: number;
    page: number;
    query: string;
    search_time_ms: number;
}

export interface ClassificationResult {
    category: string;
    confidence: number;
    probabilities: Record<string, number>;
    model_used: string;
    explanation?: string;
    message?: string;
    preprocessing_info?: {
        original_word_count: number;
        processed_token_count: number;
        tokens_removed: number;
        sample_tokens: string[];
    };
}

export interface ModelInfo {
    training_documents_count: number;
    categories: string[];
    models: {
        naive_bayes?: {
            is_trained: boolean;
            accuracy?: number;
        };
        logistic_regression?: {
            is_trained: boolean;
            accuracy?: number;
        };
    };
}

export interface CrawlStats {
    id: number;
    crawl_time: string;
    publications_count: number;
    pages_crawled: number;
    duration_seconds: number;
    target_url: string;
    status: string;
    triggered_by: string;
}

export interface CrawlerStatus {
    is_running: boolean;
    total_crawls: number;
    total_publications: number;
    schedule_info: string;
    target_url: string;
    last_crawl?: CrawlStats;
}

export interface IndexStats {
    total_documents: number;
    total_terms: number;
    unique_terms: number;
    avg_document_length: number;
    last_updated: string | null;
}

export interface ApiInfo {
    message: string;
    version: string;
    endpoints: Record<string, string>;
    documentation: string;
}
