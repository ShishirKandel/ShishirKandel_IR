"""
Classification URL Configuration

API endpoints for document classification.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('classify/', views.classify_text, name='classify'),
    path('batch-classify/', views.batch_classify, name='batch-classify'),
    path('model-info/', views.model_info, name='model-info'),
]
