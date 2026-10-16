from django.contrib import admin

from apps.core.admin import BaseAdmin, thumb

from .models import Category, GalleryImage


@admin.register(Category)
class CategoryAdmin(BaseAdmin):
    list_display = ("name", "slug", "order")
    list_editable = ("order",)
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(GalleryImage)
class GalleryImageAdmin(BaseAdmin):
    list_display = ("preview", "title", "category", "order", "is_published", "created_at")
    list_display_links = ("preview", "title")
    list_editable = ("order", "is_published")
    list_filter = ("category", "is_published")
    search_fields = ("title", "caption", "alt_text")
    readonly_fields = ("created_at", "updated_at")
    actions = ["publish", "unpublish"]

    @admin.display(description="Preview")
    def preview(self, obj):
        return thumb(obj.image)

    @admin.action(description="Publish selected images")
    def publish(self, request, queryset):
        queryset.update(is_published=True)

    @admin.action(description="Unpublish selected images")
    def unpublish(self, request, queryset):
        queryset.update(is_published=False)
