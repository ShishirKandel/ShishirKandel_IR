"""
Search Engine Models

Defines the data models for publications, authors, and the inverted index.
"""

from django.db import models


class Author(models.Model):
    """
    Represents an author of a publication.
    
    Stores author name and their profile URL on the Coventry University portal.
    """
    name = models.CharField(max_length=200)
    profile_url = models.URLField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['name', 'profile_url']
        ordering = ['name']

    def __str__(self):
        return self.name


class Publication(models.Model):
    """
    Represents a publication from Coventry University.
    
    Stores publication metadata and preprocessed searchable content.
    """
    title = models.CharField(max_length=500)
    link = models.URLField(max_length=1000, blank=True)
    abstract = models.TextField(blank=True)
    published_date = models.CharField(max_length=100, blank=True)
    authors = models.ManyToManyField(Author, related_name='publications')
    searchable_content = models.TextField(blank=True)  # Preprocessed text for indexing
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title[:100]


class InvertedIndexEntry(models.Model):
    """
    Represents an entry in the inverted index.
    
    Maps terms to publications with their TF-IDF scores.
    """
    term = models.CharField(max_length=100, db_index=True)
    publication = models.ForeignKey(
        Publication, 
        on_delete=models.CASCADE,
        related_name='index_entries'
    )
    tfidf_score = models.FloatField()
    term_frequency = models.IntegerField(default=1)

    class Meta:
        unique_together = ['term', 'publication']
        indexes = [
            models.Index(fields=['term']),
            models.Index(fields=['term', 'tfidf_score']),
        ]

    def __str__(self):
        return f"{self.term} -> {self.publication.title[:50]} ({self.tfidf_score:.4f})"
