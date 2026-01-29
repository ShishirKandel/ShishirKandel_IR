"""
Import Training Data Management Command

Imports training documents from CSV file for classification.
Usage: python manage.py import_training_data --file data/training_documents.csv
"""

import csv
from django.core.management.base import BaseCommand, CommandError
from apps.classification.models import Category, TrainingDocument


class Command(BaseCommand):
    help = 'Import training documents from CSV file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='../data/training_documents.csv',
            help='Path to the CSV file containing training documents'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing training documents before import'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        clear_existing = options['clear']
        
        # Create categories if they don't exist
        categories = {
            'business': 'Documents related to business, finance, economy, and markets',
            'entertainment': 'Documents related to movies, music, celebrities, and media',
            'health': 'Documents related to medicine, healthcare, and wellness'
        }
        
        for name, description in categories.items():
            Category.objects.get_or_create(
                name=name,
                defaults={'description': description}
            )
        
        self.stdout.write(f'Categories created/verified: {list(categories.keys())}')
        
        # Clear existing documents if requested
        if clear_existing:
            count = TrainingDocument.objects.count()
            TrainingDocument.objects.all().delete()
            self.stdout.write(f'Cleared {count} existing training documents')
        
        # Import from CSV
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                imported = 0
                
                for row in reader:
                    category_name = row['category'].strip().lower()
                    text = row['text'].strip()
                    
                    if not text:
                        continue
                    
                    try:
                        category = Category.objects.get(name=category_name)
                        TrainingDocument.objects.create(
                            text=text,
                            category=category
                        )
                        imported += 1
                    except Category.DoesNotExist:
                        self.stdout.write(self.style.WARNING(
                            f'Unknown category: {category_name}'
                        ))
                
                self.stdout.write(self.style.SUCCESS(
                    f'Successfully imported {imported} training documents'
                ))
                
                # Show count per category
                for name in categories.keys():
                    count = TrainingDocument.objects.filter(category__name=name).count()
                    self.stdout.write(f'  - {name}: {count} documents')
                    
        except FileNotFoundError:
            raise CommandError(f'File not found: {file_path}')
        except Exception as e:
            raise CommandError(f'Error importing data: {e}')
