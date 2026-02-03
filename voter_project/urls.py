"""
URL configuration for voter_project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls')),
    path('voters/', include('apps.voters.urls')),
    path('search/', include('apps.voters.public_urls')),  # Public Advanced Voter Search
]

# Serve media files in both development and production
# In production with high traffic, consider using a reverse proxy (nginx) instead
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])

# Custom error handlers
handler400 = 'apps.core.views.error_400'
handler404 = 'apps.core.views.error_404'
handler500 = 'apps.core.views.error_500'
