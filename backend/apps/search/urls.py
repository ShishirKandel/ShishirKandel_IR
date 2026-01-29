"""
Search Engine URL Configuration

API endpoints for search and index information.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('', views.api_root, name='api-root'),
    path('search/', views.search_publications, name='search'),
    path('index-info/', views.index_info, name='index-info'),
    path('index-stats/', views.index_stats, name='index-stats'),
]
