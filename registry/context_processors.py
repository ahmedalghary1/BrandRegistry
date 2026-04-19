from django.db.utils import OperationalError, ProgrammingError
from django.utils import timezone

from .models import IndustrialDesign, SiteSettings, Trademark


def global_settings(request):
    try:
        settings_obj = SiteSettings.get_solo()
        today = timezone.localdate()
        trademark_alerts = [item for item in Trademark.objects.all() if item.is_approaching_protection_expiry]
        design_alerts = [item for item in IndustrialDesign.objects.all() if item.is_approaching_protection_expiry]
    except (OperationalError, ProgrammingError):
        settings_obj = None
        trademark_alerts = []
        design_alerts = []
        today = timezone.localdate()

    return {
        "app_settings": settings_obj,
        "app_title": getattr(settings_obj, "site_title", "نظام إدارة العلامات والنماذج الصناعية"),
        "app_subtitle": getattr(
            settings_obj,
            "site_subtitle",
            "إدارة محلية متكاملة للعلامات التجارية والنماذج الصناعية",
        ),
        "current_date": today,
        "global_alert_count": len(trademark_alerts) + len(design_alerts),
    }
