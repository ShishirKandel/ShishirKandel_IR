"""
Crawler App URL Configuration

API endpoints for crawler status and manual triggers.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('crawler-status/', views.crawler_status, name='crawler-status'),
    path('trigger-crawl/', views.trigger_crawl, name='trigger-crawl'),
]
