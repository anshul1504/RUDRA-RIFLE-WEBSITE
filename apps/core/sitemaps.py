from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from apps.achievements.models import Achievement
from apps.events.models import Event
from apps.programs.models import Program

from .models import LegalPage


class StaticSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.7

    def items(self):
        from .models import SiteSettings

        site = SiteSettings.load()
        names = ["core:home", "core:about", "programs:list", "core:facilities", "admissions:enquiry", "contact:contact"]
        for flag, name in [("show_gallery", "gallery:index"), ("show_achievements", "achievements:list"),
                           ("show_events", "events:list"), ("show_booking", "bookings:slots")]:
            if getattr(site, flag):
                names.append(name)
        return names

    def location(self, item):
        return reverse(item)


class ProgramSitemap(Sitemap):
    priority = 0.8

    def items(self):
        return Program.objects.filter(is_published=True)

    def lastmod(self, obj):
        return obj.updated_at


class EventSitemap(Sitemap):
    priority = 0.6

    def items(self):
        from .models import SiteSettings

        return Event.objects.published() if SiteSettings.load().show_events else Event.objects.none()

    def lastmod(self, obj):
        return obj.updated_at


class AchievementSitemap(Sitemap):
    priority = 0.5

    def items(self):
        from .models import SiteSettings

        return Achievement.objects.filter(is_published=True) if SiteSettings.load().show_achievements else Achievement.objects.none()

    def lastmod(self, obj):
        return obj.updated_at


class LegalSitemap(Sitemap):
    priority = 0.2

    def items(self):
        return LegalPage.objects.filter(is_published=True)

    def lastmod(self, obj):
        return obj.updated_at


sitemaps = {
    "static": StaticSitemap,
    "programs": ProgramSitemap,
    "events": EventSitemap,
    "achievements": AchievementSitemap,
    "legal": LegalSitemap,
}
