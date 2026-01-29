"""
Search Engine Serializers

Serializers for API responses.
"""

from rest_framework import serializers
from .models import Author, Publication, InvertedIndexEntry


class AuthorSerializer(serializers.ModelSerializer):
    """Serializer for Author model."""
    
    class Meta:
        model = Author
        fields = ['id', 'name', 'profile_url']


class PublicationSerializer(serializers.ModelSerializer):
    """Serializer for Publication model."""
    
    authors = AuthorSerializer(many=True, read_only=True)
    relevance_score = serializers.FloatField(read_only=True, required=False)
    
    class Meta:
        model = Publication
        fields = [
            'id', 'title', 'link', 'abstract', 
            'published_date', 'authors', 'relevance_score'
        ]


class SearchResultSerializer(serializers.Serializer):
    """Serializer for search results."""
    
    results = PublicationSerializer(many=True)
    total = serializers.IntegerField()
    page = serializers.IntegerField()
    query = serializers.CharField()
    search_time_ms = serializers.FloatField()


class InvertedIndexSerializer(serializers.ModelSerializer):
    """Serializer for InvertedIndexEntry model."""
    
    publication_title = serializers.CharField(source='publication.title', read_only=True)
    
    class Meta:
        model = InvertedIndexEntry
        fields = ['term', 'publication_title', 'tfidf_score', 'term_frequency']


class IndexStatsSerializer(serializers.Serializer):
    """Serializer for index statistics."""
    
    total_documents = serializers.IntegerField()
    total_terms = serializers.IntegerField()
    unique_terms = serializers.IntegerField()
    avg_document_length = serializers.FloatField()
    last_updated = serializers.DateTimeField()
