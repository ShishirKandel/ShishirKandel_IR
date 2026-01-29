"""
Search Engine Unit Tests

Tests for the search engine components including:
- Preprocessor
- IndexBuilder
- SearchEngine
"""

from django.test import TestCase
from unittest.mock import patch, MagicMock
from apps.search.services.preprocessor import TextPreprocessor, preprocess_text, get_preprocessor
from apps.search.services.indexer import IndexBuilder


class PreprocessorTests(TestCase):
    """Tests for the TextPreprocessor class."""
    
    def setUp(self):
        self.preprocessor = TextPreprocessor()
    
    def test_basic_preprocessing(self):
        """Test basic text preprocessing."""
        text = "The Quick Brown Fox Jumps Over The Lazy Dog"
        result = self.preprocessor.preprocess(text)
        
        # Should be lowercase
        self.assertEqual(result, result.lower())
        # Should have removed stopwords
        self.assertNotIn('the', result.split())
        self.assertNotIn('over', result.split())
    
    def test_empty_input(self):
        """Test preprocessing empty input."""
        result = self.preprocessor.preprocess("")
        self.assertEqual(result, "")
    
    def test_none_input(self):
        """Test preprocessing None input."""
        result = self.preprocessor.preprocess(None)
        self.assertEqual(result, "")
    
    def test_special_characters_removed(self):
        """Test that special characters are removed."""
        text = "Hello!!! World??? Test@#$%"
        result = self.preprocessor.preprocess(text)
        
        # Should not contain special characters
        self.assertNotIn('!', result)
        self.assertNotIn('?', result)
        self.assertNotIn('@', result)
    
    def test_numbers_removed(self):
        """Test that numbers are removed."""
        text = "Test123 with 456 numbers"
        result = self.preprocessor.preprocess(text)
        
        # Should not contain digits
        self.assertFalse(any(c.isdigit() for c in result))
    
    def test_stemming_applied(self):
        """Test that stemming is applied."""
        text = "running jumps jumping runner"
        result = self.preprocessor.preprocess(text)
        
        # Stemmed forms should be present
        self.assertIn('run', result)
        self.assertIn('jump', result)
    
    def test_preprocessing_info(self):
        """Test that preprocessing info is returned correctly."""
        text = "The quick brown fox jumps"
        info = self.preprocessor.get_preprocessing_info(text)
        
        self.assertIn('original_length', info)
        self.assertIn('processed_length', info)
        self.assertIn('token_count', info)
        self.assertEqual(info['original_length'], len(text))
    
    def test_preprocess_text_function(self):
        """Test the standalone preprocess_text function."""
        text = "Testing the function"
        result = preprocess_text(text)
        
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)
    
    def test_get_preprocessor_singleton(self):
        """Test that get_preprocessor returns the same instance."""
        p1 = get_preprocessor()
        p2 = get_preprocessor()
        self.assertIs(p1, p2)


class IndexBuilderTests(TestCase):
    """Tests for the IndexBuilder class."""
    
    def setUp(self):
        self.indexer = IndexBuilder()
    
    def test_initial_state(self):
        """Test that IndexBuilder starts with empty index."""
        self.assertEqual(self.indexer.total_docs, 0)
        self.assertEqual(len(self.indexer.inverted_index), 0)
    
    def test_add_document(self):
        """Test adding a document to the index."""
        self.indexer.add_document(1, "machine learning algorithms", "ML Test")
        
        self.assertEqual(self.indexer.total_docs, 1)
        self.assertGreater(len(self.indexer.inverted_index), 0)
        
        # Check that terms are indexed
        self.assertIn('machin', self.indexer.inverted_index)
        self.assertIn('learn', self.indexer.inverted_index)
    
    def test_search_basic(self):
        """Test basic search functionality."""
        self.indexer.add_document(1, "machine learning algorithms", "ML Doc")
        self.indexer.add_document(2, "deep learning neural networks", "DL Doc")
        self.indexer.add_document(3, "data science statistics", "DS Doc")
        
        results = self.indexer.search("machine learning")
        
        self.assertGreater(len(results), 0)
        # First result should be doc 1 (exact match)
        self.assertEqual(results[0]['id'], 1)
    
    def test_search_empty_query(self):
        """Test search with empty query."""
        self.indexer.add_document(1, "test document", "Test")
        
        results = self.indexer.search("")
        self.assertEqual(len(results), 0)
    
    def test_search_no_results(self):
        """Test search with query that has no matches."""
        self.indexer.add_document(1, "machine learning", "ML")
        
        results = self.indexer.search("quantum physics")
        self.assertEqual(len(results), 0)
    
    def test_tfidf_ranking(self):
        """Test that results are ranked by TF-IDF scores."""
        self.indexer.add_document(1, "python programming language", "Python")
        self.indexer.add_document(2, "python snake reptile", "Snake")
        self.indexer.add_document(3, "python programming code software", "Code")
        
        results = self.indexer.search("python programming")
        
        # Doc 3 should rank higher (has both terms)
        self.assertEqual(results[0]['id'], 3)
    
    def test_get_stats(self):
        """Test getting index statistics."""
        self.indexer.add_document(1, "test document", "Test")
        self.indexer.add_document(2, "another document", "Another")
        
        stats = self.indexer.get_stats()
        
        self.assertEqual(stats['total_documents'], 2)
        self.assertGreater(stats['vocabulary_size'], 0)
        self.assertIn('average_doc_length', stats)


class SearchCacheTests(TestCase):
    """Tests for search caching functionality."""
    
    def test_cache_hit(self):
        """Test that repeated searches return cached results."""
        from apps.search.services.search import SearchEngine
        
        engine = SearchEngine()
        
        # First search
        result1 = engine.search("test query")
        
        # Second search should be cached
        result2 = engine.search("test query")
        
        # Results should be the same
        self.assertEqual(result1, result2)
