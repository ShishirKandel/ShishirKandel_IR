"""
Celery Tasks for Crawler App

Background tasks for scheduled and manual crawling.
"""

import logging
import os
from celery import shared_task
from django.utils import timezone

from .services.crawler import PublicationCrawler
from apps.search.services.indexer import IndexBuilder
from .models import CrawlStats

logger = logging.getLogger(__name__)


def _get_max_pages() -> int:
    """Read max pages from env; 0 or less means no limit."""
    value = os.getenv('CRAWLER_MAX_PAGES', '0')
    try:
        return int(value)
    except ValueError:
        return 0


def _use_selenium() -> bool:
    """Determine whether to use Selenium crawler by default."""
    value = os.getenv('CRAWLER_USE_SELENIUM', 'true').strip().lower()
    return value not in {'0', 'false', 'no'}


def _is_headless() -> bool:
    """Determine whether Selenium should run headless."""
    value = os.getenv('CRAWLER_HEADLESS', 'true').strip().lower()
    return value not in {'0', 'false', 'no'}


def _run_crawler(max_pages: int) -> dict:
    """
    Run the crawler with Selenium by default, falling back to requests if needed.
    """
    if _use_selenium():
        try:
            from apps.crawler.services.selenium_crawler import SeleniumPublicationCrawler

            crawler = SeleniumPublicationCrawler(
                max_pages=max_pages,
                headless=_is_headless()
            )
            logger.info("Using Selenium crawler for crawl run")
            return crawler.crawl()
        except Exception as exc:
            logger.warning(f"Selenium crawler failed, falling back to simple crawler: {exc}")

    crawler = PublicationCrawler(max_pages=max_pages)
    logger.info("Using simple requests-based crawler for crawl run")
    return crawler.crawl()


@shared_task(bind=True, max_retries=3)
def run_scheduled_crawl(self):
    """
    Scheduled task to crawl publications and rebuild index.
    
    Runs weekly as configured in settings.CELERY_BEAT_SCHEDULE
    """
    try:
        logger.info("Starting scheduled crawl...")
        
        # Create crawl stats entry
        crawl_stat = CrawlStats.objects.create(
            target_url=PublicationCrawler.BASE_URL,
            status='running',
            triggered_by='scheduled'
        )
        
        start_time = timezone.now()
        
        # Run crawler
        result = _run_crawler(_get_max_pages())
        
        # Rebuild index
        logger.info("Rebuilding search index...")
        indexer = IndexBuilder()
        index_result = indexer.build_index()
        
        # Update stats
        duration = (timezone.now() - start_time).total_seconds()
        crawl_stat.publications_count = result['new_publications']
        crawl_stat.pages_crawled = result['pages_crawled']
        crawl_stat.duration_seconds = duration
        crawl_stat.status = 'completed'
        crawl_stat.save()
        
        logger.info(f"Scheduled crawl completed. New publications: {result['new_publications']}")
        
        return {
            'status': 'success',
            'new_publications': result['new_publications'],
            'pages_crawled': result['pages_crawled'],
            'index_entries': index_result.get('entries_created', 0)
        }
        
    except Exception as exc:
        logger.error(f"Scheduled crawl failed: {exc}")
        
        # Update stats with error
        if 'crawl_stat' in locals():
            crawl_stat.status = 'failed'
            crawl_stat.error_message = str(exc)
            crawl_stat.save()
        
        # Retry in 1 hour
        self.retry(exc=exc, countdown=3600)


@shared_task
def run_manual_crawl():
    """
    Manual crawl trigger.
    
    Called via API endpoint for testing.
    """
    try:
        logger.info("Starting manual crawl...")
        
        # Create crawl stats entry
        crawl_stat = CrawlStats.objects.create(
            target_url=PublicationCrawler.BASE_URL,
            status='running',
            triggered_by='manual'
        )
        
        start_time = timezone.now()
        
        # Run crawler with fewer pages for manual trigger
        result = _run_crawler(_get_max_pages())
        
        # Rebuild index
        indexer = IndexBuilder()
        index_result = indexer.build_index()
        
        # Update stats
        duration = (timezone.now() - start_time).total_seconds()
        crawl_stat.publications_count = result['new_publications']
        crawl_stat.pages_crawled = result['pages_crawled']
        crawl_stat.duration_seconds = duration
        crawl_stat.status = 'completed'
        crawl_stat.save()
        
        logger.info(f"Manual crawl completed. New publications: {result['new_publications']}")
        
        return {
            'status': 'success',
            'crawl_id': crawl_stat.id,
            'new_publications': result['new_publications']
        }
        
    except Exception as exc:
        logger.error(f"Manual crawl failed: {exc}")
        
        if 'crawl_stat' in locals():
            crawl_stat.status = 'failed'
            crawl_stat.error_message = str(exc)
            crawl_stat.save()
        
        raise
