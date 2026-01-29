"""
Robustness Testing Management Command

Tests the classification models with various input types for viva demonstration.
Usage: python manage.py test_robustness [--output-file results.json]
"""

import json
from django.core.management.base import BaseCommand
from apps.classification.services.classifier import NaiveBayesClassifier


class Command(BaseCommand):
    help = 'Run robustness tests on classification models'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-file',
            type=str,
            default='robustness_results.json',
            help='Path to save test results'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output for each test'
        )

    def handle(self, *args, **options):
        output_file = options['output_file']
        verbose = options['verbose']
        
        self.stdout.write(self.style.WARNING('\n' + '='*60))
        self.stdout.write(self.style.WARNING('ROBUSTNESS TESTING - Classification Models'))
        self.stdout.write(self.style.WARNING('='*60 + '\n'))
        
        # Initialize classifiers
        try:
            nb_classifier = NaiveBayesClassifier()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to load models: {e}'))
            self.stdout.write(self.style.WARNING('Run: python manage.py train_models'))
            return
        
        results = {
            'short_inputs': [],
            'long_inputs': [],
            'stopword_heavy': [],
            'mixed_topics': [],
            'edge_cases': [],
            'summary': {}
        }
        
        # =====================================================
        # 6.4.1 SHORT INPUT TESTS (1-2 words)
        # =====================================================
        self.stdout.write(self.style.MIGRATE_HEADING('\n[1/5] SHORT INPUT TESTS (1-2 words)'))
        self.stdout.write('-' * 50)
        
        short_inputs = [
            ('stock market', 'business'),
            ('movie', 'entertainment'),
            ('diabetes', 'health'),
            ('revenue', 'business'),
            ('concert', 'entertainment'),
            ('surgery', 'health'),
            ('profit', 'business'),
            ('celebrity', 'entertainment'),
            ('vaccine', 'health'),
            ('investment', 'business'),
            ('actor', 'entertainment'),
            ('hospital', 'health'),
        ]
        
        for text, expected in short_inputs:
            result = self._test_classification(nb_classifier, text, expected, verbose)
            results['short_inputs'].append(result)
        
        # =====================================================
        # 6.4.2 LONG INPUT TESTS (Full Paragraphs)
        # =====================================================
        self.stdout.write(self.style.MIGRATE_HEADING('\n[2/5] LONG INPUT TESTS (Full Paragraphs)'))
        self.stdout.write('-' * 50)
        
        long_inputs = [
            (
                "The quarterly earnings report shows a significant increase in revenue. "
                "The company's stock price surged after the announcement of the merger. "
                "Analysts predict strong growth in the upcoming fiscal year with improved "
                "profit margins and market expansion strategies.",
                'business'
            ),
            (
                "The new blockbuster movie premiered at the film festival to rave reviews. "
                "The celebrity cast attended the red carpet event, and critics praised the "
                "director's innovative storytelling. The soundtrack features collaborations "
                "with Grammy-winning artists.",
                'entertainment'
            ),
            (
                "Recent medical research has shown promising results for the new cancer "
                "treatment. Clinical trials indicate improved patient outcomes with fewer "
                "side effects. The FDA is expected to review the drug application next month "
                "following positive Phase 3 results.",
                'health'
            ),
        ]
        
        for text, expected in long_inputs:
            result = self._test_classification(nb_classifier, text, expected, verbose)
            results['long_inputs'].append(result)
        
        # =====================================================
        # 6.4.3 STOPWORD-HEAVY INPUT TESTS
        # =====================================================
        self.stdout.write(self.style.MIGRATE_HEADING('\n[3/5] STOPWORD-HEAVY INPUT TESTS'))
        self.stdout.write('-' * 50)
        
        stopword_inputs = [
            ('the company is doing very well in the market', 'business'),
            ('the movie was really good and the actors were great', 'entertainment'),
            ('the patient is doing well after the treatment', 'health'),
            ('it is a very nice thing that they are doing', 'unknown'),  # Mostly stopwords
        ]
        
        for text, expected in stopword_inputs:
            result = self._test_classification(nb_classifier, text, expected, verbose)
            results['stopword_heavy'].append(result)
        
        # =====================================================
        # 6.4.4 MIXED TOPIC INPUT TESTS
        # =====================================================
        self.stdout.write(self.style.MIGRATE_HEADING('\n[4/5] MIXED TOPIC INPUT TESTS'))
        self.stdout.write('-' * 50)
        
        mixed_inputs = [
            ('Healthcare company stock rises after FDA approval', 'mixed'),
            ('Celebrity invests millions in tech startup', 'mixed'),
            ('Sports team owner announces new stadium financing', 'mixed'),
            ('Actor diagnosed with rare disease speaks out', 'mixed'),
            ('Pharmaceutical company reports record quarterly profits', 'mixed'),
        ]
        
        for text, expected in mixed_inputs:
            result = self._test_classification(nb_classifier, text, expected, verbose)
            results['mixed_topics'].append(result)
        
        # =====================================================
        # 6.4.5 EDGE CASE TESTS
        # =====================================================
        self.stdout.write(self.style.MIGRATE_HEADING('\n[5/5] EDGE CASE TESTS'))
        self.stdout.write('-' * 50)
        
        edge_cases = [
            ('', 'empty', 'Empty string'),
            ('!@#$%^&*()', 'special', 'Special characters only'),
            ('123456789', 'numbers', 'Numbers only'),
            ('a', 'single', 'Single letter'),
            ('https://example.com', 'url', 'URL only'),
            ('Bonjour le monde', 'foreign', 'Non-English text'),
            ('x ' * 500, 'long', 'Very long input (1000+ chars)'),  # Very long
            ('   ', 'whitespace', 'Whitespace only'),
            ('\n\t\r', 'control', 'Control characters'),
        ]
        
        for text, case_type, description in edge_cases:
            result = self._test_edge_case(nb_classifier, text, case_type, description, verbose)
            results['edge_cases'].append(result)
        
        # =====================================================
        # SUMMARY
        # =====================================================
        self.stdout.write(self.style.MIGRATE_HEADING('\n' + '='*60))
        self.stdout.write(self.style.MIGRATE_HEADING('TEST SUMMARY'))
        self.stdout.write(self.style.MIGRATE_HEADING('='*60))
        
        # Calculate accuracy
        total_tests = 0
        correct_nb = 0
        
        for category in ['short_inputs', 'long_inputs', 'stopword_heavy']:
            for result in results[category]:
                if result['expected'] not in ['unknown', 'mixed']:
                    total_tests += 1
                    if result['nb_result'].get('category', '').lower() == result['expected']:
                        correct_nb += 1
        
        nb_accuracy = (correct_nb / total_tests * 100) if total_tests > 0 else 0
        results['summary'] = {
            'total_tests': total_tests,
            'naive_bayes_correct': correct_nb,
            'naive_bayes_accuracy': round(nb_accuracy, 2),
            'edge_cases_handled': len([r for r in results['edge_cases'] if r['handled_gracefully']])
        }
        
        self.stdout.write(f"\nTotal Classification Tests: {total_tests}")
        self.stdout.write(f"Naive Bayes: {correct_nb}/{total_tests} correct ({nb_accuracy:.1f}%)")
        self.stdout.write(f"Edge Cases Handled: {results['summary']['edge_cases_handled']}/{len(results['edge_cases'])}")
        
        # Save results to file
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            self.stdout.write(self.style.SUCCESS(f"\nResults saved to: {output_file}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to save results: {e}"))
        
        self.stdout.write(self.style.SUCCESS('\n✅ Robustness testing complete!'))
    
    def _test_classification(self, nb, text, expected, verbose):
        """Test classification with Naive Bayes."""
        result = {
            'input': text[:100] + '...' if len(text) > 100 else text,
            'expected': expected,
            'nb_result': {}
        }

        # Test Naive Bayes
        try:
            nb_result = nb.classify(text)
            result['nb_result'] = {
                'category': nb_result.get('category', 'error'),
                'confidence': nb_result.get('confidence', 0)
            }
        except Exception as e:
            result['nb_result'] = {'category': 'error', 'error': str(e)}

        # Display result
        nb_cat = result['nb_result'].get('category', 'N/A')
        nb_conf = result['nb_result'].get('confidence', 0)
        nb_correct = nb_cat.lower() == expected.lower() if expected not in ['unknown', 'mixed'] else True

        status_nb = self.style.SUCCESS('✓') if nb_correct else self.style.ERROR('✗')

        display_text = text[:40] + '...' if len(text) > 40 else text
        self.stdout.write(f"  \"{display_text}\"")
        self.stdout.write(f"    Expected: {expected}")
        self.stdout.write(f"    NB: {nb_cat} ({nb_conf:.2f}) {status_nb}")

        return result

    def _test_edge_case(self, nb, text, case_type, description, verbose):
        """Test edge case handling."""
        result = {
            'case_type': case_type,
            'description': description,
            'input': repr(text[:50]) if len(text) > 50 else repr(text),
            'handled_gracefully': True,
            'nb_result': {}
        }

        self.stdout.write(f"  {description}:")

        # Test Naive Bayes
        try:
            nb_result = nb.classify(text)
            result['nb_result'] = {
                'category': nb_result.get('category', 'unknown'),
                'confidence': nb_result.get('confidence', 0)
            }
            self.stdout.write(
                f"    NB: {nb_result.get('category', 'N/A')} ({nb_result.get('confidence', 0):.2f}) "
                + self.style.SUCCESS('✓ Handled')
            )
        except Exception as e:
            result['nb_result'] = {'error': str(e)}
            result['handled_gracefully'] = False
            self.stdout.write(f"    NB: " + self.style.ERROR(f'ERROR - {e}'))

        return result
