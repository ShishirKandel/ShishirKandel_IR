"""
Crawler App Views

API views for crawler status and manual triggers.
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import CrawlStats
from .serializers import CrawlStatsSerializer, CrawlerStatusSerializer
from apps.search.models import Publication


@api_view(['GET'])
def crawler_status(request):
    """
    Get the current crawler status and recent crawl history.
    """
    last_crawl = CrawlStats.objects.first()
    total_crawls = CrawlStats.objects.count()
    total_publications = Publication.objects.count()
    
    # Check if any crawl is currently running
    running_crawl = CrawlStats.objects.filter(status='running').first()
    
    response_data = {
        'is_running': running_crawl is not None,
        'total_crawls': total_crawls,
        'total_publications': total_publications,
        'schedule_info': 'Weekly on Sundays at 2:00 AM UTC',
        'target_url': 'https://pureportal.coventry.ac.uk/en/organisations/ics-research-centre-for-computational-science-and-mathematical-mo/publications/'
    }
    
    if last_crawl:
        response_data['last_crawl'] = CrawlStatsSerializer(last_crawl).data
    
    if running_crawl:
        response_data['current_crawl'] = CrawlStatsSerializer(running_crawl).data
    
    return Response(response_data)


@api_view(['POST'])
def trigger_crawl(request):
    """
    Manually trigger a crawl operation.
    
    This endpoint starts a background task to crawl publications.
    """
    try:
        # Import here to avoid circular imports
        from .tasks import run_manual_crawl
        
        # Check if a crawl is already running
        running_crawl = CrawlStats.objects.filter(status='running').first()
        if running_crawl:
            return Response({
                'error': 'A crawl is already in progress',
                'current_crawl': CrawlStatsSerializer(running_crawl).data
            }, status=status.HTTP_409_CONFLICT)
        
        # Trigger async crawl task
        task = run_manual_crawl.delay()
        
        return Response({
            'message': 'Crawl task started successfully',
            'task_id': task.id,
            'status': 'pending'
        }, status=status.HTTP_202_ACCEPTED)
        
    except Exception as e:
        return Response({
            'error': str(e),
            'message': 'Failed to trigger crawl. Celery may not be running.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
