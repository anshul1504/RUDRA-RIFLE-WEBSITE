from django.contrib import admin, messages

from apps.core.admin import BaseAdmin, badge, export_csv

from .models import Slot, SlotBooking, SlotSchedule


class BookingInline(admin.TabularInline):
    model = SlotBooking
    extra = 0
    fields = ("reference", "name", "mobile", "participants", "shooting_type", "experience_level", "status")
    readonly_fields = ("reference", "name", "mobile", "participants", "shooting_type", "experience_level")
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Slot)
class SlotAdmin(BaseAdmin):
    list_display = ("date", "time_range", "title", "program", "capacity", "booked_seats", "seats_left_display", "is_published")
    list_editable = ("is_published",)
    list_filter = ("is_published", "program", "date")
    search_fields = ("title", "notes", "program__title")
    date_hierarchy = "date"
    ordering = ("date", "start_time")
    inlines = [BookingInline]
    actions = ["open_slots", "close_slots"]
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("program", "title", "date", ("start_time", "end_time"), "capacity", "is_published")}),
        ("Visitor information", {"fields": ("price_note", "notes")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).with_booked().select_related("program")

    @admin.display(description="Time")
    def time_range(self, obj):
        return f"{obj.start_time:%I:%M %p} - {obj.end_time:%I:%M %p}"

    @admin.display(description="Booked", ordering="booked")
    def booked_seats(self, obj):
        return obj.booked

    @admin.display(description="Seats left")
    def seats_left_display(self, obj):
        return badge("Full", "danger") if obj.seats_left == 0 else obj.seats_left

    @admin.action(description="Open selected slots for booking")
    def open_slots(self, request, queryset):
        queryset.update(is_published=True)

    @admin.action(description="Close selected slots (hide from website)")
    def close_slots(self, request, queryset):
        queryset.update(is_published=False)


@admin.register(SlotSchedule)
class SlotScheduleAdmin(BaseAdmin):
    list_display = ("weekday", "start_time", "end_time", "title", "program", "capacity", "is_active")
    list_editable = ("is_active",)
    list_filter = ("weekday", "is_active", "program")
    actions = ["generate_14", "generate_30"]

    def _generate(self, request, queryset, days):
        total = sum(s.generate(days) for s in queryset.filter(is_active=True))
        self.message_user(request, f"{total} new slot(s) created for the next {days} days. Existing slots were left untouched.", messages.SUCCESS)

    @admin.action(description="Generate slots for the next 14 days")
    def generate_14(self, request, queryset):
        self._generate(request, queryset, 14)

    @admin.action(description="Generate slots for the next 30 days")
    def generate_30(self, request, queryset):
        self._generate(request, queryset, 30)


@admin.register(SlotBooking)
class SlotBookingAdmin(BaseAdmin):
    list_display = ("reference", "name", "mobile", "slot", "participants", "shooting_type", "experience_level", "status_badge", "created_at")
    list_filter = ("status", "shooting_type", "experience_level", "slot__date", "slot__program")
    search_fields = ("reference", "name", "mobile", "email")
    date_hierarchy = "created_at"
    actions = ["confirm", "cancel", "mark_attended", export_csv]
    readonly_fields = ("reference", "slot", "name", "mobile", "email", "participants", "shooting_type", "experience_level", "message", "consent", "created_at", "updated_at")
    fieldsets = (
        ("Booking (as submitted)", {"fields": ("reference", "slot", "name", "mobile", "email", "participants", "shooting_type", "experience_level", "message")}),
        ("Consent & timestamps", {"fields": ("consent", "created_at", "updated_at")}),
        ("Follow-up", {"fields": ("status", "staff_notes")}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("slot", "slot__program")

    def has_add_permission(self, request):
        return False  # bookings come from the public form

    @admin.display(description="Status", ordering="status")
    def status_badge(self, obj):
        return badge(obj.get_status_display(), {"pending": "warning", "confirmed": "info", "attended": "success", "cancelled": "danger"}[obj.status])

    @staticmethod
    def _notify(booking):
        """Email the visitor when the academy confirms or cancels (only on a real change of status)."""
        from apps.core import emails

        if booking.status == SlotBooking.Status.CONFIRMED:
            emails.booking_confirmed(booking)
        elif booking.status == SlotBooking.Status.CANCELLED:
            emails.booking_cancelled(booking)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if change and "status" in form.changed_data:
            self._notify(obj)

    def _set(self, request, queryset, status, text):
        changed = list(queryset.exclude(status=status).select_related("slot", "slot__program"))
        n = queryset.update(status=status)
        for booking in changed:
            booking.status = status
            self._notify(booking)
        self.message_user(request, f"{n} booking(s) {text}.", messages.SUCCESS)

    @admin.action(description="Confirm selected bookings")
    def confirm(self, request, queryset):
        self._set(request, queryset, SlotBooking.Status.CONFIRMED, "confirmed")

    @admin.action(description="Cancel selected bookings (frees the seats)")
    def cancel(self, request, queryset):
        self._set(request, queryset, SlotBooking.Status.CANCELLED, "cancelled")

    @admin.action(description="Mark selected as Attended")
    def mark_attended(self, request, queryset):
        self._set(request, queryset, SlotBooking.Status.ATTENDED, "marked as attended")
