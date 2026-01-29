"""
Search Engine Views

API views for search functionality and index information.
"""

import time
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Avg

from .models import Publication, InvertedIndexEntry
from .serializers import (
    PublicationSerializer, 
    InvertedIndexSerializer,
    IndexStatsSerializer
)
from .services.search import SearchEngine


@api_view(['GET'])
def api_root(request):
    """
    API root endpoint - provides information about available endpoints.
    """
    return Response({
        'message': 'IR Search Engine API',
        'version': '1.0.0',
        'endpoints': {
            'search': '/api/search/?query=<search_term>',
            'index_info': '/api/index-info/',
            'index_stats': '/api/index-stats/',
            'classify': '/api/classify/',
            'batch_classify': '/api/batch-classify/',
            'model_info': '/api/model-info/',
            'crawler_status': '/api/crawler-status/',
            'trigger_crawl': '/api/trigger-crawl/',
        },
        'documentation': 'IR Search Engine for Coventry University Publications'
    })


@api_view(['GET'])
def search_publications(request):
    """
    Search publications using the inverted index.
    
    Query Parameters:
        - query: Search query string (required)
        - page: Page number for pagination (default: 1)
        - size: Results per page (default: 10)
    """
    query = request.query_params.get('query', '').strip()
    page = int(request.query_params.get('page', 1))
    size = int(request.query_params.get('size', 10))
    
    if not query:
        return Response({
            'error': 'Query parameter is required',
            'example': '/api/search/?query=machine+learning'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    start_time = time.time()
    
    try:
        search_engine = SearchEngine()
        # Fetch all matching results (up to max_results limit in SearchEngine)
        all_results = search_engine.search(query, top_n=500)
        
        # Get total count before pagination
        total_count = len(all_results)
        
        # Paginate results
        start_idx = (page - 1) * size
        end_idx = start_idx + size
        paginated_results = all_results[start_idx:end_idx]
        
        search_time_ms = (time.time() - start_time) * 1000
        
        # Serialize results
        serializer = PublicationSerializer(paginated_results, many=True)
        
        return Response({
            'results': serializer.data,
            'total': total_count,
            'page': page,
            'query': query,
            'search_time_ms': round(search_time_ms, 2)
        })
    except Exception as e:
        return Response({
            'error': str(e),
            'message': 'Search failed. Index may not be built yet.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def index_info(request):
    """
    Get sample entries from the inverted index.
    
    Query Parameters:
        - sample_size: Number of sample entries (default: 50)
    """
    sample_size = int(request.query_params.get('sample_size', 50))
    
    entries = InvertedIndexEntry.objects.select_related('publication')[:sample_size]
    serializer = InvertedIndexSerializer(entries, many=True)
    
    return Response({
        'sample_size': len(serializer.data),
        'entries': serializer.data
    })


@api_view(['GET'])
def index_stats(request):
    """
    Get statistics about the inverted index.
    """
    total_documents = Publication.objects.count()
    total_terms = InvertedIndexEntry.objects.count()
    unique_terms = InvertedIndexEntry.objects.values('term').distinct().count()
    
    # Calculate average document length
    avg_doc_length = InvertedIndexEntry.objects.values('publication').annotate(
        term_count=Count('id')
    ).aggregate(avg=Avg('term_count'))['avg'] or 0
    
    # Get last update time
    last_entry = InvertedIndexEntry.objects.order_by('-id').first()
    last_updated = last_entry.publication.updated_at if last_entry else None
    
    return Response({
        'total_documents': total_documents,
        'total_terms': total_terms,
        'unique_terms': unique_terms,
        'avg_document_length': round(avg_doc_length, 2),
        'last_updated': last_updated
    })
