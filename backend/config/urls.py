"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/

Every feature app owns its own `urls.py`; this file only mounts them under
the `/api/` prefix.
"""
from django.contrib import admin
from django.urls import include, path

from config.views import health

api_patterns = [
    path('health/', health, name='health'),
    path('auth/', include('users.auth_urls')),
    path('users/', include('users.urls')),
    path('library/', include('library.urls')),
    path('seats/', include('seats.urls')),
    path('study-rooms/', include('study_rooms.urls')),
    path('reservations/', include('reservations.urls')),
    path('notifications/', include('notifications.urls')),
    path('activity/', include('activity.urls')),
    path('reports/', include('reports.urls')),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(api_patterns)),
]
