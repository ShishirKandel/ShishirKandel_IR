"""
Train Models Management Command

Trains the Naive Bayes and Logistic Regression classification models.
Usage: python manage.py train_models
"""

from django.core.management.base import BaseCommand
from apps.classification.services.classifier import NaiveBayesClassifier
from apps.classification.services.logistic_regression import LogisticRegressionClassifier


class Command(BaseCommand):
    help = 'Train classification models (Naive Bayes and Logistic Regression)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--model',
            type=str,
            choices=['naive_bayes', 'logistic_regression', 'all'],
            default='all',
            help='Which model to train (default: all)'
        )

    def handle(self, *args, **options):
        model_type = options['model']
        
        if model_type in ['naive_bayes', 'all']:
            self.stdout.write('Training Naive Bayes classifier...')
            try:
                nb = NaiveBayesClassifier()
                result = nb.train_from_database()
                self.stdout.write(self.style.SUCCESS(
                    f"Naive Bayes trained!\n"
                    f"  Accuracy: {result['accuracy']:.4f}\n"
                    f"  Training samples: {result['train_size']}\n"
                    f"  Test samples: {result['test_size']}"
                ))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Naive Bayes training failed: {e}'))
        
        if model_type in ['logistic_regression', 'all']:
            self.stdout.write('Training Logistic Regression classifier...')
            try:
                lr = LogisticRegressionClassifier()
                result = lr.train_from_database()
                self.stdout.write(self.style.SUCCESS(
                    f"Logistic Regression trained!\n"
                    f"  Accuracy: {result['accuracy']:.4f}\n"
                    f"  Training samples: {result['train_size']}\n"
                    f"  Test samples: {result['test_size']}"
                ))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Logistic Regression training failed: {e}'))
        
        self.stdout.write(self.style.SUCCESS('Model training complete!'))
