"""
Logistic Regression Classifier

Document classification using Logistic Regression with TF-IDF vectorization.
"""

import os
import logging
import pickle
from typing import Dict, List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

from apps.search.services.preprocessor import preprocess_text, get_preprocessor

logger = logging.getLogger(__name__)

# Model save directory
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'models')


def generate_explanation(category: str, confidence: float, probabilities: Dict[str, float], model_name: str = "classifier") -> str:
    """
    Generate a human-readable explanation for the classification result.
    
    Args:
        category: Predicted category
        confidence: Confidence score (0-1)
        probabilities: Dict of category -> probability
        model_name: Name of the model used
        
    Returns:
        Human-readable explanation string
    """
    # Determine confidence level
    if confidence >= 0.8:
        conf_level = "high"
    elif confidence >= 0.6:
        conf_level = "moderate"
    else:
        conf_level = "low"
    
    # Sort alternatives
    sorted_probs = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)
    alternatives = [f"{cat}: {prob*100:.1f}%" for cat, prob in sorted_probs if cat != category]
    
    explanation = f"The {model_name} classified this text as '{category}' with {confidence*100:.1f}% confidence. "
    explanation += f"This is a {conf_level}-confidence prediction."
    
    if alternatives:
        explanation += f" Alternative classifications: {', '.join(alternatives[:2])}"
    
    return explanation


class LogisticRegressionClassifier:
    """
    Logistic Regression classifier for document classification.
    
    Categories: Business, Entertainment, Health
    """
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
        self.classifier = LogisticRegression(random_state=42, max_iter=1000)
        self.is_trained = False
        self.categories = []
        self.accuracy = None
        self._load_model()
    
    def _load_model(self):
        """Load pre-trained model if available."""
        model_path = os.path.join(MODEL_DIR, 'logistic_regression.pkl')
        
        if os.path.exists(model_path):
            try:
                with open(model_path, 'rb') as f:
                    data = pickle.load(f)
                    self.vectorizer = data['vectorizer']
                    self.classifier = data['classifier']
                    self.categories = data['categories']
                    self.accuracy = data.get('accuracy')
                    self.is_trained = True
                    logger.info("Loaded pre-trained Logistic Regression model")
            except Exception as e:
                logger.error(f"Error loading model: {e}")
    
    def _save_model(self):
        """Save trained model to file."""
        os.makedirs(MODEL_DIR, exist_ok=True)
        model_path = os.path.join(MODEL_DIR, 'logistic_regression.pkl')
        
        try:
            with open(model_path, 'wb') as f:
                pickle.dump({
                    'vectorizer': self.vectorizer,
                    'classifier': self.classifier,
                    'categories': self.categories,
                    'accuracy': self.accuracy
                }, f)
            logger.info("Saved Logistic Regression model")
        except Exception as e:
            logger.error(f"Error saving model: {e}")
    
    def train(self, texts: List[str], labels: List[str]) -> Dict:
        """
        Train the classifier on provided data.
        
        Args:
            texts: List of document texts
            labels: List of category labels
            
        Returns:
            Training results including accuracy
        """
        logger.info(f"Training Logistic Regression on {len(texts)} documents...")
        
        self.categories = list(set(labels))
        
        # Preprocess all texts
        processed_texts = [preprocess_text(text) for text in texts]
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            processed_texts, labels, test_size=0.2, random_state=42, stratify=labels
        )
        
        # Vectorize
        X_train_vec = self.vectorizer.fit_transform(X_train)
        X_test_vec = self.vectorizer.transform(X_test)
        
        # Train
        self.classifier.fit(X_train_vec, y_train)
        
        # Evaluate
        y_pred = self.classifier.predict(X_test_vec)
        self.accuracy = accuracy_score(y_test, y_pred)
        
        report = classification_report(y_test, y_pred, output_dict=True)
        
        self.is_trained = True
        self._save_model()
        
        logger.info(f"Training complete. Accuracy: {self.accuracy:.4f}")
        
        return {
            'accuracy': self.accuracy,
            'classification_report': report,
            'train_size': len(X_train),
            'test_size': len(X_test),
            'categories': self.categories
        }
    
    def train_from_database(self) -> Dict:
        """Train using documents from database."""
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
            Classification result with category, confidence, probabilities, and explanation
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
                'explanation': 'Empty or whitespace-only input cannot be classified.',
                'message': 'Empty or whitespace-only input',
                'preprocessing_info': preprocessing_info
            }
        
        if not self.is_trained:
            try:
                self.train_from_database()
            except Exception as e:
                return {
                    'category': 'unknown',
                    'confidence': 0.0,
                    'probabilities': {},
                    'explanation': f'Model not trained: {e}',
                    'message': f'Model not trained: {e}',
                    'preprocessing_info': preprocessing_info
                }
        
        # Preprocess text
        processed_text = preprocess_text(text)
        
        # Edge case: all tokens removed
        if not processed_text.strip():
            return {
                'category': 'unknown',
                'confidence': 0.0,
                'probabilities': {},
                'explanation': 'No meaningful content found after removing stopwords and special characters.',
                'message': 'No meaningful tokens after preprocessing',
                'preprocessing_info': preprocessing_info
            }
        
        try:
            # Vectorize
            text_vec = self.vectorizer.transform([processed_text])
            
            # Check for empty vector
            if text_vec.nnz == 0:
                return {
                    'category': 'unknown',
                    'confidence': 0.0,
                    'probabilities': {},
                    'explanation': 'The text contains no known vocabulary terms.',
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
            
            # Get confidence
            confidence = max(probabilities)
            
            # Generate explanation
            explanation = generate_explanation(prediction, confidence, prob_dict, "Logistic Regression")
            
            return {
                'category': prediction,
                'confidence': round(float(confidence), 4),
                'probabilities': prob_dict,
                'explanation': explanation,
                'preprocessing_info': preprocessing_info
            }
            
        except Exception as e:
            logger.error(f"Logistic Regression classification error: {e}")
            return {
                'category': 'unknown',
                'confidence': 0.0,
                'probabilities': {},
                'explanation': f'Classification error: {str(e)}',
                'message': f'Classification error: {str(e)}',
                'preprocessing_info': preprocessing_info
            }
