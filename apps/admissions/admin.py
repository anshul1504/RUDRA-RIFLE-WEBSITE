from django.contrib import admin, messages
from django.utils.html import format_html

from apps.core.admin import BaseAdmin, badge, export_csv

from .models import AdmissionEnquiry


@admin.register(AdmissionEnquiry)
class AdmissionEnquiryAdmin(BaseAdmin):
    list_display = ("applicant", "contact_links", "program", "shooting_interest", "experience_level", "status_badge", "created_at")
    list_display_links = ("applicant",)
    list_filter = ("status", "program", "shooting_interest", "experience_level", "preferred_contact", ("created_at", admin.DateFieldListFilter))
    search_fields = ("applicant_name", "guardian_name", "guardian_mobile", "email", "mobile", "city", "institution", "message")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    actions = ["mark_contacted", "mark_closed", "mark_new", export_csv]
    readonly_fields = (
        "applicant_name", "date_of_birth", "gender", "city", "institution", "guardian_name", "guardian_mobile", "email", "mobile",
        "program", "shooting_interest", "experience_level", "preferred_time", "how_heard", "preferred_contact",
        "message", "consent", "consent_at", "created_at", "updated_at", "reach_out",
    )
    fieldsets = (
        ("Applicant", {"classes": ["tab"], "fields": (
            "reach_out", ("applicant_name", "date_of_birth"), ("gender", "city"), "institution",
            ("guardian_name", "guardian_mobile"), ("mobile", "email"), "preferred_contact",
        )}),
        ("Interest", {"classes": ["tab"], "fields": (
            "program", ("shooting_interest", "experience_level"), ("preferred_time", "how_heard"), "message",
        )}),
        ("Follow-up", {"classes": ["tab"], "fields": ("status", "staff_notes")}),
        ("Consent & dates", {"classes": ["tab"], "fields": ("consent", "consent_at", "created_at", "updated_at")}),
    )

    @admin.display(description="Applicant", ordering="applicant_name")
    def applicant(self, obj):
        if obj.guardian_name:
            return format_html("<strong>{}</strong><br><small>Guardian: {}</small>", obj.applicant_name, obj.guardian_name)
        return obj.applicant_name

    @admin.display(description="Contact")
    def contact_links(self, obj):
        wa = f"https://wa.me/91{obj.mobile}"
        return format_html(
            '<a href="tel:+91{m}">{m}</a><br><a href="mailto:{e}">{e}</a> &middot; <a href="{wa}" target="_blank" rel="noopener">WhatsApp</a>',
            m=obj.mobile, e=obj.email, wa=wa,
        )

    @admin.display(description="Quick contact")
    def reach_out(self, obj):
        if not obj.pk:
            return "-"
        return format_html(
            '<a href="tel:+91{m}">Call {m}</a> &nbsp;|&nbsp; <a href="https://wa.me/91{m}" target="_blank" rel="noopener">WhatsApp</a> '
            '&nbsp;|&nbsp; <a href="mailto:{e}">Email {e}</a>', m=obj.mobile, e=obj.email,
        )

    @admin.display(description="Status", ordering="status")
    def status_badge(self, obj):
        return badge(obj.get_status_display(), {"new": "info", "contacted": "warning", "closed": "success"}[obj.status])

    def has_add_permission(self, request):
        return False  # records come only from the public form

    def _set(self, request, queryset, status, text):
        n = queryset.update(status=status)
        self.message_user(request, f"{n} enquiries marked as {text}.", messages.SUCCESS)

    @admin.action(description="Mark selected as Contacted")
    def mark_contacted(self, request, queryset):
        self._set(request, queryset, AdmissionEnquiry.Status.CONTACTED, "contacted")

    @admin.action(description="Mark selected as Closed")
    def mark_closed(self, request, queryset):
        self._set(request, queryset, AdmissionEnquiry.Status.CLOSED, "closed")

    @admin.action(description="Mark selected as New (reopen)")
    def mark_new(self, request, queryset):
        self._set(request, queryset, AdmissionEnquiry.Status.NEW, "new")
