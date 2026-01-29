"""
Naive Bayes Classifier

Document classification using Multinomial Naive Bayes with TF-IDF vectorization.
"""

import os
import logging
import pickle
from typing import Dict, List, Optional

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report, f1_score
import numpy as np

from apps.search.services.preprocessor import preprocess_text, get_preprocessor
from apps.classification.services.logistic_regression import generate_explanation

logger = logging.getLogger(__name__)

# Model save directory
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'models')


class NaiveBayesClassifier:
    """
    Naive Bayes classifier for document classification.
    
    Uses TF-IDF vectorization and Multinomial Naive Bayes.
    Categories: Business, Entertainment, Health
    """
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
        self.classifier = MultinomialNB(alpha=0.1)
        self.is_trained = False
        self.accuracy = None
        self.categories = []
        self._load_model()
    
    def _load_model(self):
        """Load pre-trained model if available."""
        model_path = os.path.join(MODEL_DIR, 'naive_bayes.pkl')
        
        if os.path.exists(model_path):
            try:
                with open(model_path, 'rb') as f:
                    data = pickle.load(f)
                    self.vectorizer = data['vectorizer']
                    self.classifier = data['classifier']
                    self.categories = data['categories']
                    self.accuracy = data.get('accuracy')
                    self.is_trained = True
                    logger.info("Loaded pre-trained Naive Bayes model")
            except Exception as e:
                logger.error(f"Error loading model: {e}")
    
    def _save_model(self):
        """Save trained model to file."""
        os.makedirs(MODEL_DIR, exist_ok=True)
        model_path = os.path.join(MODEL_DIR, 'naive_bayes.pkl')
        
        try:
            with open(model_path, 'wb') as f:
                pickle.dump({
                    'vectorizer': self.vectorizer,
                    'classifier': self.classifier,
                    'categories': self.categories,
                    'accuracy': self.accuracy
                }, f)
            logger.info("Saved Naive Bayes model")
        except Exception as e:
            logger.error(f"Error saving model: {e}")
    
    def train(self, texts: List[str], labels: List[str], test_size: float = 0.2) -> Dict:
        """
        Train the classifier on the provided data.
        
        Args:
            texts: List of document texts
            labels: List of category labels
            test_size: Proportion of data for testing
            
        Returns:
            Training results including accuracy
        """
        logger.info(f"Training Naive Bayes on {len(texts)} documents...")
        
        # Preprocess all texts
        processed_texts = [preprocess_text(text) for text in texts]
        
        # Get unique categories
        self.categories = list(set(labels))
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            processed_texts, labels, test_size=test_size, random_state=42, stratify=labels
        )
        
        # Vectorize
        X_train_vec = self.vectorizer.fit_transform(X_train)
        X_test_vec = self.vectorizer.transform(X_test)
        
        # Train classifier
        self.classifier.fit(X_train_vec, y_train)
        
        # Evaluate
        predictions = self.classifier.predict(X_test_vec)
        self.accuracy = accuracy_score(y_test, predictions)

        # Calculate F1 score
        f1 = f1_score(y_test, predictions, average='micro')

        # Generate confusion matrix
        conf_matrix = confusion_matrix(y_test, predictions, labels=self.classifier.classes_)

        # Generate classification report
        class_report = classification_report(y_test, predictions, output_dict=True)
        class_report_text = classification_report(y_test, predictions)

        self.is_trained = True
        self._save_model()

        logger.info(f"Training complete. Accuracy: {self.accuracy:.4f}, F1: {f1:.4f}")
        logger.info(f"\nClassification Report:\n{class_report_text}")
        logger.info(f"\nConfusion Matrix:\n{conf_matrix}")

        return {
            'status': 'success',
            'accuracy': self.accuracy,
            'f1_score': f1,
            'train_size': len(X_train),
            'test_size': len(X_test),
            'categories': self.categories,
            'confusion_matrix': conf_matrix.tolist(),
            'confusion_matrix_labels': list(self.classifier.classes_),
            'classification_report': class_report,
            'classification_report_text': class_report_text
        }
    
    def train_from_database(self) -> Dict:
        """
        Train the classifier using training documents from the database.
        """
        from apps.classification.models import TrainingDocument
        
        documents = TrainingDocument.objects.select_related('category').all()
        
        if documents.count() < 10:
            raise ValueError(f"Not enough training documents. Found {documents.count()}, need at least 10.")
        
        texts = [doc.text for doc in documents]
        labels = [doc.category.name for doc in documents]
        
        return self.train(texts, labels)
    
    def classify(self, text: str) -> Dict:
        """
        Classify a document.
        
        Args:
            text: Input text to classify
            
        Returns:
            Classification result with category, confidence, and probabilities
        """
        # Handle None input
        if text is None:
            text = ""
        
        # Get preprocessing info
        preprocessor = get_preprocessor()
        preprocessing_info = preprocessor.get_preprocessing_info(text)
        
        # Edge case: empty or whitespace-only input
        if not text or not text.strip():
            return {
                'category': 'unknown',
                'confidence': 0.0,
                'probabilities': {},
                'message': 'Empty or whitespace-only input',
                'preprocessing_info': preprocessing_info
            }
        
        if not self.is_trained:
            # Try to train from database
            try:
                self.train_from_database()
            except Exception as e:
                return {
                    'category': 'unknown',
                    'confidence': 0.0,
                    'probabilities': {},
                    'message': f'Model not trained: {e}',
                    'preprocessing_info': preprocessing_info
                }
        
        # Preprocess text
        processed_text = preprocess_text(text)
        
        # Edge case: all tokens removed by preprocessing
        if not processed_text.strip():
            return {
                'category': 'unknown',
                'confidence': 0.0,
                'probabilities': {},
                'message': 'No meaningful tokens after preprocessing (stopwords/special chars only)',
                'preprocessing_info': preprocessing_info
            }
        
        try:
            # Vectorize
            text_vec = self.vectorizer.transform([processed_text])
            
            # Check if vector is all zeros (unknown vocabulary)
            if text_vec.nnz == 0:
                return {
                    'category': 'unknown',
                    'confidence': 0.0,
                    'probabilities': {},
                    'message': 'No known vocabulary terms found',
                    'preprocessing_info': preprocessing_info
                }
            
            # Predict
            prediction = self.classifier.predict(text_vec)[0]
            probabilities = self.classifier.predict_proba(text_vec)[0]
            
            # Create probability dictionary
            prob_dict = {}
            for i, category in enumerate(self.classifier.classes_):
                prob_dict[category] = round(float(probabilities[i]), 4)
            
            # Get confidence (max probability)
            confidence = max(probabilities)
            
            # Generate explanation
            explanation = generate_explanation(prediction, confidence, prob_dict, "Naive Bayes")
            
            return {
                'category': prediction,
                'confidence': round(float(confidence), 4),
                'probabilities': prob_dict,
                'explanation': explanation,
                'preprocessing_info': preprocessing_info
            }
            
        except Exception as e:
            logger.error(f"Classification error: {e}")
            return {
                'category': 'unknown',
                'confidence': 0.0,
                'probabilities': {},
                'message': f'Classification error: {str(e)}',
                'preprocessing_info': preprocessing_info
            }
