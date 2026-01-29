"""
Import Publications Management Command

Imports publications from a JSON file.
Usage: python manage.py import_publications --file data/publications.json
"""

import json
from django.core.management.base import BaseCommand, CommandError
from apps.search.models import Author, Publication


class Command(BaseCommand):
    help = 'Import publications from a JSON file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            required=True,
            help='Path to the JSON file containing publications'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing publications before import'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        clear_existing = options['clear']
        
        # Clear existing data if requested
        if clear_existing:
            pub_count = Publication.objects.count()
            author_count = Author.objects.count()
            Publication.objects.all().delete()
            Author.objects.all().delete()
            self.stdout.write(f'Cleared {pub_count} publications and {author_count} authors')
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            raise CommandError(f'File not found: {file_path}')
        except json.JSONDecodeError as e:
            raise CommandError(f'Invalid JSON: {e}')
        
        # Handle both array of publications and object with 'publications' key
        if isinstance(data, list):
            publications = data
        elif isinstance(data, dict) and 'publications' in data:
            publications = data['publications']
        else:
            raise CommandError('JSON must be an array or object with "publications" key')
        
        imported = 0
        skipped = 0
        
        for pub_data in publications:
            title = pub_data.get('title', '').strip()
            if not title:
                skipped += 1
                continue
            
            # Check if publication already exists
            if Publication.objects.filter(title=title).exists():
                skipped += 1
                continue
            
            # Create publication
            publication = Publication.objects.create(
                title=title,
                link=pub_data.get('link', ''),
                abstract=pub_data.get('abstract', ''),
                published_date=pub_data.get('published_date', '')
            )
            
            # Handle authors
            authors_data = pub_data.get('authors', [])
            for author_data in authors_data:
                if isinstance(author_data, str):
                    author_name = author_data
                    profile_url = ''
                elif isinstance(author_data, dict):
                    author_name = author_data.get('name', '')
                    # Handle both 'profile_url' and 'profile' keys
                    profile_url = author_data.get('profile_url', '') or author_data.get('profile', '') or ''
                else:
                    continue
                
                if not author_name:
                    continue
                
                author, _ = Author.objects.get_or_create(
                    name=author_name,
                    defaults={'profile_url': profile_url}
                )
                publication.authors.add(author)
            
            imported += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'Import complete!\n'
            f'  Imported: {imported} publications\n'
            f'  Skipped: {skipped} (duplicates or empty)\n'
            f'  Total in database: {Publication.objects.count()} publications'
        ))
