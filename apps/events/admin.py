from django.contrib import admin

from apps.core.admin import BaseAdmin

from .models import Event, EventPhoto


class EventPhotoInline(admin.TabularInline):
    model = EventPhoto
    extra = 1
    fields = ("image", "alt_text", "caption", "order")


@admin.register(Event)
class EventAdmin(BaseAdmin):
    list_display = ("title", "start_at", "end_at", "location", "is_published")
    list_editable = ("is_published",)
    list_filter = ("is_published", "start_at")
    search_fields = ("title", "summary", "description", "location")
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "start_at"
    inlines = [EventPhotoInline]
    readonly_fields = ("created_at", "updated_at")
