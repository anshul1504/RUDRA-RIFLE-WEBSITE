from django.contrib import admin

from apps.core.admin import BaseAdmin, thumb

from .models import Program, ProgramHighlight


class HighlightInline(admin.TabularInline):
    model = ProgramHighlight
    extra = 1


@admin.register(Program)
class ProgramAdmin(BaseAdmin):
    list_display = ("image_preview", "title", "allow_booking", "order", "is_published", "updated_at")
    list_display_links = ("image_preview", "title")
    list_editable = ("order", "is_published")
    list_filter = ("is_published", "allow_booking")
    search_fields = ("title", "summary", "description")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [HighlightInline]
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Content", {"classes": ["tab"], "fields": ("title", "slug", "summary", "description", "icon", "is_published", "order")}),
        ("Photo", {"classes": ["tab"], "fields": ("image", "image_alt", "image_focus")}),
        ("Optional details", {"classes": ["tab"], "fields": ("age_eligibility", "duration", "batch_timings", "fees"),
            "description": "Shown on the site only when filled in. Leave blank until the academy confirms them."}),
        ("Slot booking", {"classes": ["tab"], "fields": ("allow_booking",)}),
        ("Timestamps", {"classes": ["tab"], "fields": ("created_at", "updated_at")}),
    )

    @admin.display(description="Photo")
    def image_preview(self, obj):
        return thumb(obj.image)
