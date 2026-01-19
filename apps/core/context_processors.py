from django.conf import settings as django_settings


def global_context(request):
    """Global context processor for all templates."""
    
    # Application name from settings or default
    app_name = getattr(django_settings, 'APP_NAME', 'Voter Management System')
    
    return {
        'APP_NAME': app_name,
    }
