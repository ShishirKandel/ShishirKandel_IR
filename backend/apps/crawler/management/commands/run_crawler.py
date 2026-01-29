"""
Run Crawler Management Command

Manually triggers the web crawler to fetch publications.
Usage: python manage.py run_crawler [--max-pages N] [--use-simple]

By default, uses Selenium crawler which can bypass Cloudflare protection.
Use --use-simple flag to use the simple requests-based crawler (may fail due to Cloudflare).
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.crawler.models import CrawlStats
from apps.search.services.indexer import IndexBuilder


class Command(BaseCommand):
    help = 'Run the web crawler to fetch publications from Coventry University'

    def add_arguments(self, parser):
        parser.add_argument(
            '--max-pages',
            type=int,
            default=0,
            help='Maximum number of pages to crawl (0 = no limit)'
        )
        index_group = parser.add_mutually_exclusive_group()
        index_group.add_argument(
            '--rebuild-index',
            action='store_true',
            help='Rebuild the search index after crawling (default: enabled)'
        )
        index_group.add_argument(
            '--skip-index',
            action='store_true',
            help='Skip index rebuild after crawling'
        )
        parser.add_argument(
            '--use-simple',
            action='store_true',
            help='Use simple requests-based crawler instead of Selenium (may fail with Cloudflare)'
        )
        parser.add_argument(
            '--headless',
            action='store_true',
            default=True,
            help='Run Selenium in headless mode (default: True)'
        )
        parser.add_argument(
            '--no-headless',
            action='store_true',
            help='Run Selenium with visible browser window (for debugging)'
        )
        parser.add_argument(
            '--list-workers',
            type=int,
            default=4,
            help='Number of parallel workers for listing pages (default: 4)'
        )
        parser.add_argument(
            '--detail-workers',
            type=int,
            default=8,
            help='Number of parallel workers for detail pages (default: 8)'
        )

    def handle(self, *args, **options):
        max_pages = options['max_pages']
        rebuild_index = not options['skip_index']
        use_simple = options['use_simple']
        headless = not options.get('no_headless', False)
        list_workers = options['list_workers']
        detail_workers = options['detail_workers']
        
        if use_simple:
            self.stdout.write(
                self.style.WARNING('Using simple crawler (may fail with Cloudflare protection)')
            )
            from apps.crawler.services.crawler import PublicationCrawler
            crawler_name = 'Simple'
        else:
            self.stdout.write(
                self.style.SUCCESS('Using Selenium crawler (bypasses Cloudflare)')
            )
            from apps.crawler.services.selenium_crawler import SeleniumPublicationCrawler
            crawler_name = 'Selenium'
        
        max_label = max_pages if max_pages > 0 else 'auto'
        self.stdout.write(f'Starting {crawler_name} crawler (max pages: {max_label})...')
        start_time = timezone.now()
        
        try:
            # Run crawler
            if use_simple:
                crawler = PublicationCrawler(max_pages=max_pages)
                base_url = crawler.base_url
            else:
                crawler = SeleniumPublicationCrawler(
                    max_pages=max_pages,
                    headless=headless,
                    list_workers=list_workers,
                    detail_workers=detail_workers
                )
                from apps.crawler.services.selenium_crawler import BASE_URL
                base_url = BASE_URL
            
            result = crawler.crawl()
            
            duration = (timezone.now() - start_time).total_seconds()
            
            # Save crawl stats
            CrawlStats.objects.create(
                publications_count=result.get('new_publications', 0),
                pages_crawled=result.get('pages_crawled', 0),
                duration_seconds=duration,
                target_url=base_url,
                status='completed',
                triggered_by='manual'
            )
            
            self.stdout.write(self.style.SUCCESS(
                f"\nCrawl completed!\n"
                f"  Crawler: {crawler_name}\n"
                f"  Pages crawled: {result.get('pages_crawled', 0)}\n"
                f"  Publications found: {result.get('publications_found', result.get('new_publications', 0))}\n"
                f"  New publications: {result.get('new_publications', 0)}\n"
                f"  Duration: {duration:.2f}s"
            ))
            
            # Optionally rebuild index
            if rebuild_index:
                self.stdout.write('Rebuilding search index...')
                indexer = IndexBuilder()
                index_result = indexer.build_index()
                self.stdout.write(self.style.SUCCESS(
                    f"Index rebuilt: {index_result.get('entries_created', 0)} entries"
                ))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Crawler failed: {e}'))
            
            # Save failed crawl stats
            from apps.crawler.services.selenium_crawler import BASE_URL
            CrawlStats.objects.create(
                publications_count=0,
                pages_crawled=0,
                duration_seconds=(timezone.now() - start_time).total_seconds(),
                target_url=BASE_URL,
                status='failed',
                error_message=str(e),
                triggered_by='manual'
            )
            raise
