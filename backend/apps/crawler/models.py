"""
Crawler App Models

Defines the data models for tracking crawl statistics.
"""

from django.db import models


class CrawlStats(models.Model):
    """
    Records statistics for each crawl operation.
    
    Tracks both manual and scheduled crawls with their results.
    """
    TRIGGER_CHOICES = [
        ('manual', 'Manual'),
        ('scheduled', 'Scheduled'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    crawl_time = models.DateTimeField(auto_now_add=True)
    publications_count = models.IntegerField(default=0)
    pages_crawled = models.IntegerField(default=0)
    duration_seconds = models.FloatField(default=0)
    target_url = models.URLField(max_length=500)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='completed')
    triggered_by = models.CharField(max_length=50, choices=TRIGGER_CHOICES, default='manual')
    error_message = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'Crawl Stats'
        ordering = ['-crawl_time']

    def __str__(self):
        return f"Crawl at {self.crawl_time.strftime('%Y-%m-%d %H:%M')} - {self.status}"
