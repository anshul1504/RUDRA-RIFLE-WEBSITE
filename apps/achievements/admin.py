from django.contrib import admin

from apps.core.admin import BaseAdmin

from .models import Achievement


@admin.register(Achievement)
class AchievementAdmin(BaseAdmin):
    list_display = ("title", "athlete_name", "date", "order", "is_published")
    list_editable = ("order", "is_published")
    list_filter = ("is_published", "date")
    search_fields = ("title", "summary", "description", "athlete_name")
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "date"
    readonly_fields = ("created_at", "updated_at")
