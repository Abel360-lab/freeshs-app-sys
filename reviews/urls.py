"""
URL configuration for reviews app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'reviews'

# API Router
router = DefaultRouter()
router.register(r'admin/reviews', views.ReviewViewSet, basename='admin-reviews')

urlpatterns = [
    # Admin API endpoints
    path('', include(router.urls)),
]
