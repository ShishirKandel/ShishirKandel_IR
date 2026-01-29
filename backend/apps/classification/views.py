"""
Classification Views

API views for document classification.
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import Category, TrainingDocument
from .serializers import (
    ClassificationRequestSerializer,
    ClassificationResultSerializer,
    ModelInfoSerializer
)
from .services.classifier import NaiveBayesClassifier
from .services.logistic_regression import LogisticRegressionClassifier


# Global classifier instances (lazy loaded)
_naive_bayes = None
_logistic_regression = None


def get_naive_bayes():
    """Get or create Naive Bayes classifier instance."""
    global _naive_bayes
    if _naive_bayes is None:
        _naive_bayes = NaiveBayesClassifier()
    return _naive_bayes


def get_logistic_regression():
    """Get or create Logistic Regression classifier instance."""
    global _logistic_regression
    if _logistic_regression is None:
        _logistic_regression = LogisticRegressionClassifier()
    return _logistic_regression

@api_view(['POST'])
def classify_text(request):
    """
    Classify input text using Naive Bayes or Logistic Regression.
    
    Request Body:
        - text: Text to classify (required)
        - model_type: 'naive_bayes' or 'logistic_regression' (default: 'naive_bayes')
    """
    serializer = ClassificationRequestSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    text = serializer.validated_data['text']
    model_type = serializer.validated_data['model_type']
    
    try:
        if model_type == 'naive_bayes':
            classifier = get_naive_bayes()
        elif model_type == 'logistic_regression':
            classifier = get_logistic_regression()
        
        result = classifier.classify(text)
        
        return Response({
            'category': result['category'],
            'confidence': result['confidence'],
            'probabilities': result.get('probabilities', {}),
            'model_used': model_type,
            'explanation': result.get('explanation', ''),
            'message': result.get('message', ''),
            'preprocessing_info': result.get('preprocessing_info', {})
        })
        
    except Exception as e:
        return Response({
            'category': 'unknown',
            'confidence': 0.0,
            'probabilities': {},
            'model_used': model_type,
            'error': str(e),
            'message': 'Classification failed. Model may not be trained yet.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def batch_classify(request):
    """
    Batch classify multiple texts for robustness testing.
    
    Request Body:
        - texts: List of texts to classify
        - model_type: 'naive_bayes' (default: 'naive_bayes')
    """
    texts = request.data.get('texts', [])
    model_type = request.data.get('model_type', 'naive_bayes')
    
    if not texts:
        return Response({'error': 'No texts provided'}, status=status.HTTP_400_BAD_REQUEST)
    
    if model_type != 'naive_bayes':
        return Response({'error': 'Unsupported model_type'}, status=status.HTTP_400_BAD_REQUEST)
    
    results = []
    
    for text in texts[:50]:  # Limit to 50 texts
        result_item = {'input': text[:200]}  # Truncate display
        
        try:
            nb = get_naive_bayes()
            nb_result = nb.classify(text)
            result_item['naive_bayes'] = {
                'category': nb_result['category'],
                'confidence': nb_result['confidence']
            }
        except Exception as e:
            result_item['naive_bayes'] = {'error': str(e)}
        
        results.append(result_item)
    
    return Response({
        'total': len(results),
        'results': results
    })


@api_view(['GET'])
def model_info(request):
    """
    Get information about the classification models.
    
    Query Parameters:
        - model_type: 'naive_bayes' or 'logistic_regression' (optional)
    """
    model_type = request.query_params.get('model_type', 'both')
    
    categories = list(Category.objects.values_list('name', flat=True))
    training_count = TrainingDocument.objects.count()
    
    response_data = {
        'training_documents_count': training_count,
        'categories': categories,
        'models': {}
    }
    
    if model_type in ['naive_bayes', 'both']:
        try:
            nb = get_naive_bayes()
            response_data['models']['naive_bayes'] = {
                'is_trained': nb.is_trained,
                'accuracy': getattr(nb, 'accuracy', None)
            }
        except Exception as e:
            response_data['models']['naive_bayes'] = {
                'is_trained': False,
                'error': str(e)
            }

    if model_type in ['logistic_regression', 'both']:
        try:
            lr = get_logistic_regression()
            response_data['models']['logistic_regression'] = {
                'is_trained': lr.is_trained,
                'accuracy': getattr(lr, 'accuracy', None)
            }
        except Exception as e:
            response_data['models']['logistic_regression'] = {
                'is_trained': False,
                'error': str(e)
            }
    
    return Response(response_data)
