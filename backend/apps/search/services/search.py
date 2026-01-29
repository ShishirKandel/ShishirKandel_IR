"""
Search Engine

Provides search functionality using the inverted index with TF-IDF ranking.
"""

import logging
from collections import defaultdict
from functools import lru_cache
from typing import List

from django.db.models import Sum
from ..models import Publication, InvertedIndexEntry
from .preprocessor import preprocess_text

logger = logging.getLogger(__name__)


class SearchEngine:
    """
    Search engine that uses the inverted index for retrieval.
    
    Features:
    - Query preprocessing (same as document preprocessing)
    - TF-IDF based relevance ranking
    - Result caching for performance
    """
    
    def __init__(self):
        self.min_score_threshold = 0.01
        self.max_results = 500
    
    def search(self, query: str, top_n: int = 10) -> List[Publication]:
        """
        Search publications using the query.
        
        Args:
            query: Search query string
            top_n: Maximum number of results to return
            
        Returns:
            List of Publication objects with relevance_score attribute
        """
        if not query or not query.strip():
            return []
        
        # Preprocess query
        query_tokens = preprocess_text(query, return_tokens=True)
        
        if not query_tokens:
            logger.warning(f"Query '{query}' produced no tokens after preprocessing")
            return []
        
        logger.info(f"Searching for tokens: {query_tokens}")
        
        # Find matching index entries
        matching_entries = InvertedIndexEntry.objects.filter(
            term__in=query_tokens
        ).select_related('publication')
        
        if not matching_entries.exists():
            logger.info("No matching entries found in index")
            return []
        
        # Calculate document scores by summing TF-IDF scores
        doc_scores = defaultdict(float)
        doc_objects = {}
        
        for entry in matching_entries:
            doc_scores[entry.publication_id] += entry.tfidf_score
            doc_objects[entry.publication_id] = entry.publication
        
        # Filter by minimum score threshold
        filtered_docs = {
            doc_id: score for doc_id, score in doc_scores.items()
            if score >= self.min_score_threshold
        }
        
        if not filtered_docs:
            return []
        
        # Sort by score (descending)
        sorted_docs = sorted(
            filtered_docs.items(),
            key=lambda x: x[1],
            reverse=True
        )[:min(top_n, self.max_results)]
        
        # Build result list with scores
        results = []
        for doc_id, score in sorted_docs:
            pub = doc_objects[doc_id]
            pub.relevance_score = round(score, 4)
            results.append(pub)
        
        logger.info(f"Found {len(results)} results for query '{query}'")
        return results
    
    def search_with_details(self, query: str, top_n: int = 10) -> dict:
        """
        Search with additional details about the search process.
        
        Useful for debugging and understanding search results.
        """
        query_tokens = preprocess_text(query, return_tokens=True)
        
        results = self.search(query, top_n)
        
        # Get term coverage information
        matched_terms = set()
        for pub in results:
            entries = InvertedIndexEntry.objects.filter(
                publication=pub,
                term__in=query_tokens
            ).values_list('term', flat=True)
            matched_terms.update(entries)
        
        return {
            'results': results,
            'query_tokens': query_tokens,
            'matched_terms': list(matched_terms),
            'unmatched_terms': list(set(query_tokens) - matched_terms),
            'total_results': len(results)
        }


class SearchCache:
    """
    Simple in-memory cache for search results.
    
    Uses LRU (Least Recently Used) eviction policy.
    """
    
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self._cache = {}
    
    @lru_cache(maxsize=100)
    def get_cached_search(self, query: str, top_n: int) -> tuple:
        """
        Get cached search results.
        
        Returns tuple of publication IDs for cache efficiency.
        """
        engine = SearchEngine()
        results = engine.search(query, top_n)
        return tuple(pub.id for pub in results)
    
    def clear_cache(self):
        """Clear the search cache."""
        self.get_cached_search.cache_clear()
