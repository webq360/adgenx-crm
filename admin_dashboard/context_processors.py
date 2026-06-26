from .models import SiteSettings

def site_settings(request):
    """Add site settings to all templates"""
    settings = SiteSettings.get()
    return {
        'settings': settings,
    }
