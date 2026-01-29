"""
URL configuration for config.

API Endpoints:
- /admin/ - Django admin
- /api/ - REST API (search, classification, crawler)
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apps.search.urls')),
    path('api/', include('apps.classification.urls')),
    path('api/', include('apps.crawler.urls')),
]
