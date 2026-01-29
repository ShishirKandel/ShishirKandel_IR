"""
Django management command to display the confusion matrix.

Usage: python manage.py show_confusion_matrix
"""

from django.core.management.base import BaseCommand
from apps.classification.services.print_confusion_matrix import print_confusion_matrix


class Command(BaseCommand):
    help = 'Train the Naive Bayes classifier and display the confusion matrix'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Generating confusion matrix...'))
        result = print_confusion_matrix()
        self.stdout.write(self.style.SUCCESS('Done!'))
