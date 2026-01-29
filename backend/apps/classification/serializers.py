"""
Classification Serializers

Serializers for classification API requests and responses.
"""

from rest_framework import serializers
from .models import Category, TrainingDocument


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model."""
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']


class TrainingDocumentSerializer(serializers.ModelSerializer):
    """Serializer for TrainingDocument model."""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = TrainingDocument
        fields = ['id', 'text', 'category', 'category_name', 'created_at']


class ClassificationRequestSerializer(serializers.Serializer):
    """Serializer for classification requests."""
    
    text = serializers.CharField(required=True, min_length=1)
    model_type = serializers.ChoiceField(
        choices=['naive_bayes', 'logistic_regression'],
        default='naive_bayes'
    )


class ClassificationResultSerializer(serializers.Serializer):
    """Serializer for classification results."""
    
    category = serializers.CharField()
    confidence = serializers.FloatField()
    probabilities = serializers.DictField(child=serializers.FloatField())
    model_used = serializers.CharField()
    explanation = serializers.CharField(required=False)
    preprocessing_info = serializers.DictField(required=False)


class ModelInfoSerializer(serializers.Serializer):
    """Serializer for model information."""
    
    model_type = serializers.CharField()
    is_trained = serializers.BooleanField()
    training_documents_count = serializers.IntegerField()
    categories = serializers.ListField(child=serializers.CharField())
    accuracy = serializers.FloatField(required=False)
    last_trained = serializers.DateTimeField(required=False)
