import csv

from django.contrib import admin
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html

from .models import Announcement, ContentItem, Faq, Facility, HeroSlide, InstagramReel, LegalPage, MenuItem, SiteSettings, Testimonial


def thumb(image, size=56):
    if not image:
        return "-"
    return format_html('<img src="{}" alt="" style="height:{}px;width:auto;border-radius:4px;display:block">', image.url, size)


@admin.action(description="Export selected to CSV")
def export_csv(modeladmin, request, queryset):
    """Download the selected rows as a CSV file (useful for enquiries and bookings)."""
    fields = [f for f in modeladmin.model._meta.fields if f.name not in {"staff_notes"}]
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{modeladmin.model._meta.model_name}.csv"'
    response.write("﻿")  # BOM so Excel opens UTF-8 correctly
    writer = csv.writer(response)
    writer.writerow([f.verbose_name for f in fields])
    for obj in queryset:
        writer.writerow([
            str(getattr(obj, f"get_{f.name}_display")() if f.choices else (getattr(obj, f.name) or "")) for f in fields
        ])
    return response


TONES = {"info": ("#6b3505", "#ffffff"), "warning": ("#f0a73a", "#24232B"), "success": ("#2e7d32", "#ffffff"),
         "danger": ("#b3261e", "#ffffff"), "muted": ("#e5e3ee", "#24232B")}


def badge(text, tone="info"):
    """Small coloured status pill for list pages."""
    bg, fg = TONES[tone]
    return format_html(
        '<span style="background:{};color:{};padding:2px 10px;border-radius:999px;font-size:12px;font-weight:600;white-space:nowrap">{}</span>',
        bg, fg, text,
    )


class BaseAdmin(admin.ModelAdmin):
    """Shared admin behaviour."""

    list_per_page = 25
    save_on_top = True


@admin.register(SiteSettings)
class SiteSettingsAdmin(BaseAdmin):
    fieldsets = (
        ("Contact", {"classes": ["tab"], "fields": (
            "organisation_name", "tagline", "city", "state", "address", "phone", "whatsapp_number", "email",
            "website", "opening_hours", "contact_image", "contact_image_alt",
        )}),
        ("Hero (no-slide fallback)", {"classes": ["tab"], "fields": (
            "hero_image", "hero_image_alt", "hero_eyebrow", "hero_headline", "hero_headline_accent", "hero_subheadline",
            "hero_tagline", "hero_primary_cta", "hero_secondary_cta",
        )}),
        ("Page text", {"classes": ["tab"], "fields": (
            "intro_heading", "about_intro", "about_mission_text", "vision_text", "mission_text", "safety_heading", "safety_text",
            "responsible_text", "cta_heading", "cta_text", "footer_description", "about_image", "about_image_alt",
        )}),
        ("Slot booking", {"classes": ["tab"], "fields": ("booking_intro", "booking_days_ahead", "booking_payment_note")}),
        ("Page switches", {"classes": ["tab"], "fields": ("show_achievements", "show_events", "show_gallery", "show_booking"),
            "description": "Turn whole sections of the website on or off. A switched-off page returns Not Found and its links disappear."}),
        ("Map & social", {"classes": ["tab"], "fields": (
            "map_embed_url", "map_link_url", "facebook_url", "instagram_url", "youtube_url", "x_url",
        )}),
    )

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        # There is only one settings record: go straight to it.
        return redirect(reverse("admin:core_sitesettings_change", args=[SiteSettings.load().pk]))


@admin.register(HeroSlide)
class HeroSlideAdmin(BaseAdmin):
    list_display = ("preview", "headline", "headline_accent", "primary_label", "order", "is_published")
    list_display_links = ("preview", "headline")
    list_editable = ("order", "is_published")
    list_filter = ("is_published",)
    search_fields = ("headline", "headline_accent", "text", "eyebrow")
    ordering = ("order",)
    fieldsets = (
        ("Slide text", {"fields": ("eyebrow", "headline", "headline_accent", "text", "is_published", "order")}),
        ("Image", {"fields": ("image", "image_alt")}),
        ("Buttons", {"fields": (("primary_label", "primary_link"), ("secondary_label", "secondary_link"))}),
    )

    @admin.display(description="Image")
    def preview(self, obj):
        return thumb(obj.image, 44)


@admin.register(MenuItem)
class MenuItemAdmin(BaseAdmin):
    """Show/hide header menu items. Items cannot be added or deleted here, and hiding never removes a page."""

    list_display = ("label", "points_to", "is_visible")
    list_display_links = ("label",)
    list_editable = ("is_visible",)
    fields = ("label", "is_visible")
    readonly_fields = ("label",)
    ordering = ("order",)
    list_per_page = 50

    @admin.display(description="Page")
    def points_to(self, obj):
        from django.urls import reverse

        return reverse(obj.url_name)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(InstagramReel)
class InstagramReelAdmin(BaseAdmin):
    list_display = ("preview", "title", "url", "order", "is_published")
    list_display_links = ("preview", "title")
    list_editable = ("order", "is_published")
    list_filter = ("is_published",)
    search_fields = ("title", "url")
    fieldsets = (
        (None, {"fields": ("title", "url", "thumbnail", "thumbnail_alt", "order", "is_published")}),
    )

    @admin.display(description="Cover")
    def preview(self, obj):
        return thumb(obj.thumbnail, 56)


@admin.register(Announcement)
class AnnouncementAdmin(BaseAdmin):
    list_display = ("text", "link_label", "is_published", "created_at")
    list_editable = ("is_published",)


@admin.register(Testimonial)
class TestimonialAdmin(BaseAdmin):
    list_display = ("name", "role", "order", "is_published")
    list_editable = ("order", "is_published")
    list_filter = ("is_published",)
    search_fields = ("name", "quote")


@admin.register(Faq)
class FaqAdmin(BaseAdmin):
    list_display = ("question", "order", "is_published")
    list_editable = ("order", "is_published")
    search_fields = ("question", "answer")


@admin.register(Facility)
class FacilityAdmin(BaseAdmin):
    list_display = ("preview", "title", "icon", "order", "is_published", "updated_at")
    list_display_links = ("preview", "title")
    list_editable = ("order", "is_published")
    list_filter = ("is_published",)
    search_fields = ("title", "description")

    @admin.display(description="Photo")
    def preview(self, obj):
        return thumb(obj.image)


@admin.register(ContentItem)
class ContentItemAdmin(BaseAdmin):
    list_display = ("title", "kind", "icon", "order", "is_published")
    list_editable = ("order", "is_published")
    list_filter = ("kind", "is_published")
    search_fields = ("title", "text")
    ordering = ("kind", "order")


@admin.register(LegalPage)
class LegalPageAdmin(BaseAdmin):
    list_display = ("title", "slug", "last_reviewed", "is_published", "updated_at")
    list_filter = ("is_published",)
    search_fields = ("title", "body")
    prepopulated_fields = {"slug": ("title",)}
