from django.urls import path
from . import views

app_name = 'voters'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('voters/', views.voter_list, name='voter_list'),
    path('voters/<int:pk>/', views.voter_detail, name='voter_detail'),
    path('voters/<int:pk>/update-status/', views.update_voter_status, name='update_voter_status'),
    path('categories/', views.category_list, name='category_list'),
    path('categories/<int:pk>/', views.category_detail, name='category_detail'),
    path('audit/', views.audit_log, name='audit_log'),
    path('api/categories/', views.api_categories, name='api_categories'),
    path('api/search/', views.api_search_voters, name='api_search_voters'),
    path('api/suggestions/', views.api_search_suggestions, name='api_search_suggestions'),
]
