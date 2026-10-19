from django.conf import settings
from django.utils import timezone

from .menu import build_menu
from .models import Announcement, SiteSettings


def site(request):
    site = SiteSettings.load()
    nav_items, nav_cta, menu = build_menu(request, site)
    return {
        "site": site,
        "nav_items": nav_items,
        "nav_cta": nav_cta,
        "menu": menu,
        "announcement": Announcement.objects.filter(is_published=True).first(),
        "developer_credit": settings.DEVELOPER_CREDIT,
        "SITE_URL": settings.SITE_URL,
        "canonical_url": settings.SITE_URL + request.path,
        "launch_staff_notice": _launch_notice(request, site),
    }


def _launch_notice(request, site):
    """For logged-in staff only: explain why they see the site while visitors still see the countdown."""
    user = getattr(request, "user", None)
    if not (user and user.is_staff and site.launch_countdown_enabled and site.launch_at):
        return None
    return site.launch_at if site.launch_at > timezone.now() else None



def admin_dashboard(request):
    """Adds dashboard widgets (counts, today's slots, quick links) to the admin index page only."""
    if request.path != "/admin/" or not request.user.is_authenticated or not request.user.is_staff:
        return {}
    from .dashboard import dashboard_callback

    return dashboard_callback(request, {})
