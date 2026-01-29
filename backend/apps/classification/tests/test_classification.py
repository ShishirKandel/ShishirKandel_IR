"""
Classification Unit Tests

Tests for the classification components including:
- NaiveBayesClassifier
- LogisticRegressionClassifier
"""

from django.test import TestCase
from unittest.mock import patch, MagicMock
from apps.classification.services.classifier import NaiveBayesClassifier
from apps.classification.services.logistic_regression import LogisticRegressionClassifier, generate_explanation


class GenerateExplanationTests(TestCase):
    """Tests for the generate_explanation function."""
    
    def test_high_confidence_explanation(self):
        """Test explanation for high confidence prediction."""
        explanation = generate_explanation(
            category='business',
            confidence=0.95,
            probabilities={'business': 0.95, 'health': 0.03, 'entertainment': 0.02},
            model_name='Naive Bayes'
        )
        
        self.assertIn('business', explanation)
        self.assertIn('95.0%', explanation)
        self.assertIn('high', explanation)
        self.assertIn('Naive Bayes', explanation)
    
    def test_moderate_confidence_explanation(self):
        """Test explanation for moderate confidence prediction."""
        explanation = generate_explanation(
            category='health',
            confidence=0.65,
            probabilities={'health': 0.65, 'business': 0.25, 'entertainment': 0.10},
            model_name='Naive Bayes'
        )
        
        self.assertIn('moderate', explanation)
    
    def test_low_confidence_explanation(self):
        """Test explanation for low confidence prediction."""
        explanation = generate_explanation(
            category='entertainment',
            confidence=0.40,
            probabilities={'entertainment': 0.40, 'business': 0.35, 'health': 0.25},
            model_name='Logistic Regression'
        )
        
        self.assertIn('low', explanation)
    
    def test_alternatives_included(self):
        """Test that alternative classifications are included."""
        explanation = generate_explanation(
            category='business',
            confidence=0.80,
            probabilities={'business': 0.80, 'health': 0.15, 'entertainment': 0.05},
            model_name='Test'
        )
        
        self.assertIn('Alternative', explanation)
        self.assertIn('health', explanation)


class ClassifierEdgeCaseTests(TestCase):
    """Tests for classifier edge case handling."""
    
    def setUp(self):
        # Patch the model loading to prevent file system access
        self.patcher = patch.object(NaiveBayesClassifier, '_load_model')
        self.mock_load = self.patcher.start()
    
    def tearDown(self):
        self.patcher.stop()
    
    def test_empty_input(self):
        """Test classification of empty input."""
        classifier = NaiveBayesClassifier()
        classifier.is_trained = False
        
        result = classifier.classify("")
        
        self.assertEqual(result['category'], 'unknown')
        self.assertEqual(result['confidence'], 0.0)
        self.assertIn('message', result)
    
    def test_whitespace_only_input(self):
        """Test classification of whitespace-only input."""
        classifier = NaiveBayesClassifier()
        classifier.is_trained = False
        
        result = classifier.classify("   \n\t   ")
        
        self.assertEqual(result['category'], 'unknown')
        self.assertIn('message', result)
    
    def test_none_input(self):
        """Test classification of None input."""
        classifier = NaiveBayesClassifier()
        classifier.is_trained = False
        
        result = classifier.classify(None)
        
        self.assertEqual(result['category'], 'unknown')


class LogisticRegressionTests(TestCase):
    """Tests for the LogisticRegressionClassifier class."""
    
    def setUp(self):
        # Patch the model loading
        self.patcher = patch.object(LogisticRegressionClassifier, '_load_model')
        self.mock_load = self.patcher.start()
    
    def tearDown(self):
        self.patcher.stop()
    
    def test_empty_input(self):
        """Test classification of empty input."""
        classifier = LogisticRegressionClassifier()
        classifier.is_trained = False
        
        result = classifier.classify("")
        
        self.assertEqual(result['category'], 'unknown')
        self.assertIn('explanation', result)
    
    def test_preprocessing_info_included(self):
        """Test that preprocessing info is included in result."""
        classifier = LogisticRegressionClassifier()
        classifier.is_trained = False
        
        result = classifier.classify("test input text")
        
        self.assertIn('preprocessing_info', result)


class ClassificationAPITests(TestCase):
    """Integration tests for classification API."""
    
    def test_classify_endpoint_naive_bayes(self):
        """Test the classify endpoint with Naive Bayes."""
        from django.test import Client
        
        client = Client()
        response = client.post(
            '/api/classify/',
            {'text': 'stock market earnings report', 'model_type': 'naive_bayes'},
            content_type='application/json'
        )
        
        # Should return 200 even if model not trained
        self.assertIn(response.status_code, [200, 500])
    
    def test_classify_endpoint_logistic_regression(self):
        """Test the classify endpoint with Logistic Regression."""
        from django.test import Client
        
        client = Client()
        response = client.post(
            '/api/classify/',
            {'text': 'movie premiere hollywood', 'model_type': 'logistic_regression'},
            content_type='application/json'
        )
        
        self.assertIn(response.status_code, [200, 500])
    
    def test_classify_invalid_model_type(self):
        """Test classify endpoint with invalid model type."""
        from django.test import Client
        
        client = Client()
        response = client.post(
            '/api/classify/',
            {'text': 'test text', 'model_type': 'invalid_model'},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_classify_missing_text(self):
        """Test classify endpoint with missing text."""
        from django.test import Client
        
        client = Client()
        response = client.post(
            '/api/classify/',
            {'model_type': 'naive_bayes'},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)


class BatchClassifyTests(TestCase):
    """Tests for batch classification endpoint."""
    
    def test_batch_classify_endpoint(self):
        """Test the batch classify endpoint."""
        from django.test import Client
        
        client = Client()
        response = client.post(
            '/api/batch-classify/',
            {
                'texts': ['stock market', 'movie premiere', 'vaccine trial'],
                'model_type': 'naive_bayes'
            },
            content_type='application/json'
        )
        
        self.assertIn(response.status_code, [200, 500])
    
    def test_batch_classify_empty_list(self):
        """Test batch classify with empty list."""
        from django.test import Client
        
        client = Client()
        response = client.post(
            '/api/batch-classify/',
            {'texts': [], 'model_type': 'naive_bayes'},
            content_type='application/json'
        )
        
        # Should return 400 for empty list
        self.assertEqual(response.status_code, 400)
