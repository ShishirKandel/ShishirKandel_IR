"""
Build Index Management Command

Builds the inverted index from publications in the database.
Usage: python manage.py build_index
"""

from django.core.management.base import BaseCommand
from apps.search.services.indexer import IndexBuilder


class Command(BaseCommand):
    help = 'Build the inverted index from publications'

    def handle(self, *args, **options):
        self.stdout.write('Building inverted index...')
        
        indexer = IndexBuilder()
        result = indexer.build_index()
        
        if result['status'] == 'success':
            self.stdout.write(self.style.SUCCESS(
                f"Index built successfully!\n"
                f"Documents indexed: {result['documents_indexed']}\n"
                f"Index entries created: {result['entries_created']}\n"
                f"Unique terms: {result['unique_terms']}"
            ))
        elif result['status'] == 'no_documents':
            self.stdout.write(self.style.WARNING(
                'No publications found. Import publications first using run_crawler command.'
            ))
        else:
            self.stdout.write(self.style.ERROR(f"Index build failed: {result}"))
