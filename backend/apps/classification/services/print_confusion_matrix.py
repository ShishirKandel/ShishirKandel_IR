"""
Confusion Matrix Visualization Script

Run this script to generate and display the confusion matrix for the Naive Bayes classifier.
Usage: python manage.py shell < apps/classification/services/print_confusion_matrix.py
Or run directly in Django shell.
"""

import os
import sys

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

import numpy as np


def print_confusion_matrix():
    """
    Train the model and print confusion matrix with detailed metrics.
    """
    from apps.classification.services.classifier import NaiveBayesClassifier

    print("=" * 70)
    print("NAIVE BAYES CLASSIFIER - CONFUSION MATRIX ANALYSIS")
    print("=" * 70)

    # Initialize and train classifier
    classifier = NaiveBayesClassifier()

    print("\nTraining classifier from database...")
    result = classifier.train_from_database()

    print("\n" + "-" * 70)
    print("TRAINING RESULTS")
    print("-" * 70)
    print(f"Status: {result['status']}")
    print(f"Training samples: {result['train_size']}")
    print(f"Testing samples: {result['test_size']}")
    print(f"Categories: {', '.join(result['categories'])}")

    print("\n" + "-" * 70)
    print("MODEL EVALUATION METRICS")
    print("-" * 70)
    print(f"Accuracy = {result['accuracy']:.4f}")
    print(f"F1 Score = {result['f1_score']:.4f}")

    print("\n" + "-" * 70)
    print("CLASSIFICATION REPORT")
    print("-" * 70)
    print(result['classification_report_text'])

    print("\n" + "-" * 70)
    print("CONFUSION MATRIX")
    print("-" * 70)

    # Get confusion matrix data
    conf_matrix = np.array(result['confusion_matrix'])
    labels = result['confusion_matrix_labels']

    # Print matrix header
    print("\nPredicted Labels (columns) vs True Labels (rows)")
    print()

    # Calculate column widths
    max_label_len = max(len(label) for label in labels)
    col_width = max(max_label_len + 2, 12)

    # Print header row
    header = " " * (max_label_len + 2)
    for label in labels:
        header += f"{label:^{col_width}}"
    print(header)
    print("-" * len(header))

    # Print each row
    for i, row_label in enumerate(labels):
        row_str = f"{row_label:<{max_label_len + 2}}"
        for j, val in enumerate(conf_matrix[i]):
            row_str += f"{val:^{col_width}}"
        print(row_str)

    print("\n" + "-" * 70)
    print("CONFUSION MATRIX INTERPRETATION")
    print("-" * 70)

    for i, label in enumerate(labels):
        tp = conf_matrix[i, i]
        fp = sum(conf_matrix[:, i]) - tp
        fn = sum(conf_matrix[i, :]) - tp
        tn = conf_matrix.sum() - tp - fp - fn

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0

        print(f"\n{label}:")
        print(f"  True Positives (TP):  {tp:4d} - Correctly classified as {label}")
        print(f"  False Positives (FP): {fp:4d} - Incorrectly classified as {label}")
        print(f"  False Negatives (FN): {fn:4d} - {label} misclassified as other")
        print(f"  True Negatives (TN):  {tn:4d} - Correctly NOT classified as {label}")
        print(f"  Precision: {precision:.4f}")
        print(f"  Recall:    {recall:.4f}")

    print("\n" + "=" * 70)
    print("END OF CONFUSION MATRIX ANALYSIS")
    print("=" * 70)

    return result


if __name__ == "__main__":
    # Setup Django
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()

    print_confusion_matrix()
