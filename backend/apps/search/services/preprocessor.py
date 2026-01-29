"""
Text Preprocessor

Provides text preprocessing utilities for search and classification.
Includes tokenization, stemming, and stopword removal using NLTK.
"""

import re
import nltk
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab', quiet=True)

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)


class TextPreprocessor:
    """
    Text preprocessor for normalizing and tokenizing text.
    
    Processing steps:
    1. Convert to lowercase
    2. Remove punctuation and special characters
    3. Tokenize using NLTK
    4. Remove stopwords
    5. Apply Porter stemming
    """
    
    def __init__(self):
        self.stemmer = PorterStemmer()
        try:
            self.stop_words = set(stopwords.words('english'))
        except LookupError:
            # Fallback when NLTK data is unavailable (offline or not downloaded).
            self.stop_words = set(ENGLISH_STOP_WORDS)
    
    def preprocess(self, text: str, return_tokens: bool = False) -> str | list:
        """
        Preprocess text for indexing or searching.
        
        Args:
            text: Input text to preprocess
            return_tokens: If True, return list of tokens instead of string
            
        Returns:
            Preprocessed text as string or list of tokens
        """
        if not text or not isinstance(text, str):
            return [] if return_tokens else ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'https?://\S+|www\.\S+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove punctuation and special characters, keep alphanumeric
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Tokenize
        try:
            tokens = word_tokenize(text)
        except Exception:
            tokens = text.split()
        
        # Remove stopwords and apply stemming
        processed_tokens = []
        for token in tokens:
            # Skip short tokens and stopwords
            if len(token) < 2 or token in self.stop_words:
                continue
            
            # Skip pure numbers
            if token.isdigit():
                continue
            
            # Apply stemming
            stemmed = self.stemmer.stem(token)
            processed_tokens.append(stemmed)
        
        if return_tokens:
            return processed_tokens
        
        return ' '.join(processed_tokens)
    
    def get_preprocessing_info(self, text: str) -> dict:
        """
        Get detailed information about the preprocessing steps.
        
        Useful for debugging and understanding classification results.
        """
        original_words = len(text.split()) if text else 0
        tokens = self.preprocess(text, return_tokens=True)
        
        return {
            'original_word_count': original_words,
            'processed_token_count': len(tokens),
            'tokens_removed': original_words - len(tokens),
            'sample_tokens': tokens[:10]  # First 10 tokens
        }


# Global preprocessor instance
_preprocessor = None

def get_preprocessor() -> TextPreprocessor:
    """Get or create the global preprocessor instance."""
    global _preprocessor
    if _preprocessor is None:
        _preprocessor = TextPreprocessor()
    return _preprocessor


def preprocess_text(text: str, return_tokens: bool = False) -> str | list:
    """Convenience function for preprocessing text."""
    return get_preprocessor().preprocess(text, return_tokens)
