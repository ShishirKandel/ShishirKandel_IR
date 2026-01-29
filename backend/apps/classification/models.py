"""
Classification Models

Defines the data models for document classification categories and training data.
"""

from django.db import models


class Category(models.Model):
    """
    Represents a classification category.
    
    Categories: Business, Entertainment, Health
    """
    CATEGORY_CHOICES = [
        ('business', 'Business'),
        ('entertainment', 'Entertainment'),
        ('health', 'Health'),
    ]
    
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class TrainingDocument(models.Model):
    """
    Represents a training document for classification.
    
    Each document belongs to a single category and is used to train
    the Naive Bayes and Logistic Regression classifiers.
    """
    text = models.TextField()
    category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE,
        related_name='training_documents'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.category.name}: {self.text[:50]}..."
