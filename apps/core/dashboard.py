"""Context for the custom admin dashboard (see templates/admin/index.html)."""
from django.urls import reverse
from django.utils import timezone

from apps.admissions.models import AdmissionEnquiry
from apps.bookings.models import Slot, SlotBooking
from apps.contact.models import ContactMessage


def dashboard_callback(request, context):
    user = request.user
    today = timezone.localdate()

    def link(app, model):
        return reverse(f"admin:{app}_{model}_changelist")

    kpis = []
    if user.has_perm("bookings.view_slotbooking"):
        pending = SlotBooking.objects.filter(status="pending").count()
        kpis.append({"title": "Pending slot bookings", "value": pending, "fa": "fa-ticket-alt",
                     "url": link("bookings", "slotbooking") + "?status__exact=pending", "hot": pending > 0})
        upcoming = Slot.objects.filter(date__gte=today, is_published=True).count()
        kpis.append({"title": "Open upcoming slots", "value": upcoming, "fa": "fa-calendar-check", "url": link("bookings", "slot"), "hot": False})
    if user.has_perm("admissions.view_admissionenquiry"):
        new = AdmissionEnquiry.objects.filter(status="new").count()
        kpis.append({"title": "New admission enquiries", "value": new, "fa": "fa-user-plus",
                     "url": link("admissions", "admissionenquiry") + "?status__exact=new", "hot": new > 0})
    if user.has_perm("contact.view_contactmessage"):
        new = ContactMessage.objects.filter(status="new").count()
        kpis.append({"title": "New contact messages", "value": new, "fa": "fa-envelope",
                     "url": link("contact", "contactmessage") + "?status__exact=new", "hot": new > 0})

    context.update({
        "kpis": kpis,
        "recent_bookings": SlotBooking.objects.select_related("slot").order_by("-created_at")[:6] if user.has_perm("bookings.view_slotbooking") else [],
        "recent_enquiries": AdmissionEnquiry.objects.order_by("-created_at")[:6] if user.has_perm("admissions.view_admissionenquiry") else [],
        "todays_slots": Slot.objects.filter(date=today).with_booked().order_by("start_time") if user.has_perm("bookings.view_slot") else [],
        "quick_links": [
            ("Homepage carousel", "fa-images", reverse("admin:core_heroslide_changelist")),
            ("Header menu visibility", "fa-bars", reverse("admin:core_menuitem_changelist")),
            ("Edit homepage text & contact details", "fa-sliders-h", reverse("admin:core_sitesettings_changelist")),
            ("Programs", "fa-bullseye", link("programs", "program")),
            ("Upload gallery photos", "fa-photo-video", reverse("admin:gallery_galleryimage_add")),
            ("Add an event", "fa-calendar-alt", reverse("admin:events_event_add")),
            ("Add an achievement", "fa-trophy", reverse("admin:achievements_achievement_add")),
            ("Weekly slot schedule", "fa-redo", link("bookings", "slotschedule")),
        ],
    })
    return context
