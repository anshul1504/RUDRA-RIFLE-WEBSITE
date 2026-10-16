import random

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET
from django.views.generic import TemplateView

from apps.achievements.models import Achievement
from apps.bookings.models import Slot
from apps.events.models import Event
from apps.gallery.models import GalleryImage
from apps.programs.models import Program

from .models import ContentItem, Facility, Faq, HeroSlide, LegalPage, Testimonial


def items(kind):
    return ContentItem.objects.filter(kind=kind, is_published=True)


class HomeView(TemplateView):
    template_name = "core/home.html"

    @staticmethod
    def gallery_preview():
        """A shuffled, always-full grid: 12 photos (fits 2, 3 and 4 columns); fewer photos are trimmed to full rows of 4."""
        photos = list(GalleryImage.objects.filter(is_published=True).select_related("category"))
        random.shuffle(photos)
        keep = 12 if len(photos) >= 12 else len(photos) // 4 * 4 or len(photos)
        return photos[:keep]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            programs=Program.objects.filter(is_published=True).prefetch_related("highlights")[:4],
            facilities=Facility.objects.filter(is_published=True)[:6],
            gallery_images=self.gallery_preview(),
            upcoming_events=Event.objects.upcoming()[:3],
            achievements=Achievement.objects.filter(is_published=True)[:3],
            slides=HeroSlide.objects.filter(is_published=True),
            testimonials=Testimonial.objects.filter(is_published=True)[:6],
            faqs=Faq.objects.filter(is_published=True)[:6],
            why_choose=items(ContentItem.Kind.WHY),
            achievement_themes=items(ContentItem.Kind.FOCUS),
            next_slots=[sl for sl in Slot.objects.open_for_booking().with_booked()[:12] if sl.is_bookable][:3],
            pay_and_play=Program.objects.filter(is_published=True, allow_booking=True).first(),
            meta_description=(
                "Professional rifle and pistol shooting training for beginners and competitive shooters at "
                "Rudra Sports Rifle Shooting Society, Indore, Madhya Pradesh."
            ),
        )
        return ctx


class AboutView(TemplateView):
    template_name = "core/about.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            mission_points=items(ContentItem.Kind.MISSION),
            core_values=items(ContentItem.Kind.VALUE),
            why_choose=items(ContentItem.Kind.WHY),
            programs=Program.objects.filter(is_published=True).prefetch_related("highlights")[:4],
            facilities=Facility.objects.filter(is_published=True)[:6],
            meta_description="About Rudra Sports Rifle Shooting Society, Indore: our vision, mission and values of discipline, focus, confidence and sportsmanship.",
        )
        return ctx


class FacilitiesView(TemplateView):
    template_name = "core/facilities.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["facilities"] = Facility.objects.filter(is_published=True)
        ctx["meta_description"] = "Facilities at Rudra Sports Rifle Shooting Society, Indore, as stated by the academy."
        return ctx


def legal_page(request, slug):
    page = get_object_or_404(LegalPage, slug=slug, is_published=True)
    return render(request, "core/legal.html", {"page": page, "meta_description": f"{page.title} - Rudra Sports Rifle Shooting Society, Indore."})


@require_GET
def robots_txt(request):
    from django.conf import settings
    from django.urls import reverse

    lines = [
        "User-agent: *",
        "Disallow: /admin/",
        "Disallow: /media/private/",
        f"Sitemap: {settings.SITE_URL}{reverse('django.contrib.sitemaps.views.sitemap')}",
    ]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain")


def error_404(request, exception=None):
    return render(request, "404.html", status=404)


def error_500(request):
    return render(request, "500.html", status=500)
