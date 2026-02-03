"""
Public URL routes for Advanced Voter Search.
These routes do not require authentication.
"""
from django.urls import path
from . import public_views

app_name = 'public_search'

urlpatterns = [
    path('', public_views.advanced_voter_search, name='advanced_search'),
    path('api/categories/', public_views.public_api_categories, name='api_categories'),
    path('api/search/', public_views.public_api_search_voters, name='api_search'),
    path('api/suggestions/', public_views.public_api_suggestions, name='api_suggestions'),
    path('api/slip/<int:pk>/', public_views.public_voter_slip, name='voter_slip'),
]
