from django.contrib import admin, messages

from apps.core.admin import BaseAdmin, badge, export_csv

from .models import ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(BaseAdmin):
    list_display = ("subject", "name", "email", "phone", "status_badge", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("name", "email", "subject", "message")
    date_hierarchy = "created_at"
    actions = ["mark_replied", "mark_closed", export_csv]
    readonly_fields = ("name", "email", "phone", "subject", "message", "consent", "created_at", "updated_at")
    fieldsets = (
        ("Message (as submitted)", {"fields": ("name", "email", "phone", "subject", "message")}),
        ("Consent & timestamps", {"fields": ("consent", "created_at", "updated_at")}),
        ("Follow-up", {"fields": ("status", "staff_notes")}),
    )

    @admin.display(description="Status", ordering="status")
    def status_badge(self, obj):
        return badge(obj.get_status_display(), {"new": "info", "replied": "warning", "closed": "success"}[obj.status])

    def has_add_permission(self, request):
        return False

    @admin.action(description="Mark selected as Replied")
    def mark_replied(self, request, queryset):
        n = queryset.update(status=ContactMessage.Status.REPLIED)
        self.message_user(request, f"{n} messages marked as replied.", messages.SUCCESS)

    @admin.action(description="Mark selected as Closed")
    def mark_closed(self, request, queryset):
        n = queryset.update(status=ContactMessage.Status.CLOSED)
        self.message_user(request, f"{n} messages marked as closed.", messages.SUCCESS)
