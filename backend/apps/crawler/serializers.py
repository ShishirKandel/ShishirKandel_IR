"""
Crawler App Serializers

Serializers for crawler status API responses.
"""

from rest_framework import serializers
from .models import CrawlStats


class CrawlStatsSerializer(serializers.ModelSerializer):
    """Serializer for CrawlStats model."""
    
    class Meta:
        model = CrawlStats
        fields = [
            'id', 'crawl_time', 'publications_count', 'pages_crawled',
            'duration_seconds', 'target_url', 'status', 'triggered_by',
            'error_message'
        ]


class CrawlerStatusSerializer(serializers.Serializer):
    """Serializer for overall crawler status."""
    
    is_running = serializers.BooleanField()
    last_crawl = CrawlStatsSerializer(required=False)
    total_crawls = serializers.IntegerField()
    total_publications = serializers.IntegerField()
    schedule_info = serializers.CharField()
