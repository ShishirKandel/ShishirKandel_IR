"""
Inverted Index Builder

Builds and manages the inverted index with TF-IDF scoring.
"""

import logging
from collections import defaultdict
from math import log
from django.db import transaction

from ..models import Publication, InvertedIndexEntry
from .preprocessor import preprocess_text

logger = logging.getLogger(__name__)


class IndexBuilder:
    """
    Builds an inverted index from publications.
    
    Uses TF-IDF (Term Frequency-Inverse Document Frequency) scoring
    to rank the relevance of terms in documents.
    """
    
    def __init__(self):
        self.documents = []
        self.term_doc_freq = defaultdict(int)  # Number of docs containing each term
        self.doc_term_freq = {}  # Term frequencies per document
    
    def build_index(self):
        """
        Build the inverted index from all publications in the database.
        
        This method:
        1. Clears existing index entries
        2. Preprocesses all publication content
        3. Calculates TF-IDF scores
        4. Stores index entries in the database
        """
        logger.info("Starting index build...")
        
        # Get all publications
        publications = Publication.objects.all()
        total_docs = publications.count()
        
        if total_docs == 0:
            logger.warning("No publications found. Index not built.")
            return {'status': 'no_documents', 'entries_created': 0}
        
        logger.info(f"Building index for {total_docs} publications...")
        
        # Clear existing index
        InvertedIndexEntry.objects.all().delete()
        
        # Calculate term frequencies for each document
        doc_terms = {}
        for pub in publications:
            # Combine title and abstract for indexing
            content = f"{pub.title} {pub.abstract}"
            tokens = preprocess_text(content, return_tokens=True)
            
            # Count term frequencies in this document
            term_freq = defaultdict(int)
            for token in tokens:
                term_freq[token] += 1
                self.term_doc_freq[token] += 1
            
            doc_terms[pub.id] = term_freq
            
            # Update publication's searchable content
            pub.searchable_content = ' '.join(tokens)
            pub.save(update_fields=['searchable_content'])
        
        # Calculate TF-IDF and create index entries
        entries_to_create = []
        
        for pub_id, term_freq in doc_terms.items():
            for term, freq in term_freq.items():
                # TF = term frequency in document
                tf = freq
                
                # IDF = log(total_docs / docs_containing_term)
                doc_freq = self.term_doc_freq[term]
                idf = log(total_docs / doc_freq) if doc_freq > 0 else 0
                
                # TF-IDF score
                tfidf = tf * idf
                
                entries_to_create.append(
                    InvertedIndexEntry(
                        term=term,
                        publication_id=pub_id,
                        tfidf_score=tfidf,
                        term_frequency=freq
                    )
                )
        
        # Bulk create entries
        with transaction.atomic():
            InvertedIndexEntry.objects.bulk_create(entries_to_create, batch_size=1000)
        
        logger.info(f"Index built successfully. Created {len(entries_to_create)} entries.")
        
        return {
            'status': 'success',
            'documents_indexed': total_docs,
            'entries_created': len(entries_to_create),
            'unique_terms': len(self.term_doc_freq)
        }
    
    def update_index(self, publication: Publication):
        """
        Update the index for a single publication.
        
        Useful when a new publication is added or an existing one is updated.
        """
        # Remove existing entries for this publication
        InvertedIndexEntry.objects.filter(publication=publication).delete()
        
        # Get total document count
        total_docs = Publication.objects.count()
        
        # Preprocess content
        content = f"{publication.title} {publication.abstract}"
        tokens = preprocess_text(content, return_tokens=True)
        
        # Calculate term frequencies
        term_freq = defaultdict(int)
        for token in tokens:
            term_freq[token] += 1
        
        # Update searchable content
        publication.searchable_content = ' '.join(tokens)
        publication.save(update_fields=['searchable_content'])
        
        # Create index entries
        entries = []
        for term, freq in term_freq.items():
            # Get document frequency for this term
            doc_freq = InvertedIndexEntry.objects.filter(term=term).values('publication').distinct().count() + 1
            
            # Calculate TF-IDF
            tf = freq
            idf = log(total_docs / doc_freq) if doc_freq > 0 else 0
            tfidf = tf * idf
            
            entries.append(
                InvertedIndexEntry(
                    term=term,
                    publication=publication,
                    tfidf_score=tfidf,
                    term_frequency=freq
                )
            )
        
        InvertedIndexEntry.objects.bulk_create(entries)
        
        return {'status': 'success', 'entries_created': len(entries)}
