"""Branded HTML emails (with a plain-text twin) for every message the website sends.

Who gets what:
  * Admission enquiry  -> academy (alert, reply-to = the applicant) + applicant ("thank you, we will get back to you")
  * Contact message    -> academy (alert, reply-to = the sender)    + sender    ("thank you, we will get back to you")
  * Slot booking       -> academy (alert) + visitor ("request received"), then the visitor again when the academy
                          confirms or cancels the booking in the admin panel.
Nothing else is emailed. Every function is safe to call: a mail problem is logged and never breaks the visitor's page.
"""
import logging
from datetime import datetime

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from .models import SiteSettings

logger = logging.getLogger(__name__)


def _context(**extra):
    site = SiteSettings.load()
    base = settings.SITE_URL.rstrip("/")
    ctx = {"site": site, "site_url": base, "logo_url": f"{base}/static/images/rudra-logo.png",
           "year": timezone.localdate().year, "button": None, "note": "", "greeting": "", "paragraphs": [], "details": []}
    ctx.update(extra)
    return ctx


def _send(subject, to, ctx, reply_to=None):
    if not to:
        return False
    html = render_to_string("emails/base.html", ctx)
    text = render_to_string("emails/base.txt", ctx)
    try:
        msg = EmailMultiAlternatives(subject, text, settings.DEFAULT_FROM_EMAIL, list(to), reply_to=list(reply_to or []))
        msg.attach_alternative(html, "text/html")
        msg.send(fail_silently=False)
        return True
    except Exception:  # noqa: BLE001 - never break the visitor's submission
        logger.exception("Could not send email %r", subject)
        return False


def _staff(subject, ctx, reply_to=None):
    return _send(subject, settings.ENQUIRY_NOTIFY_EMAILS, ctx, reply_to)


def _admin_url(name, pk):
    return settings.SITE_URL.rstrip("/") + reverse(name, args=[pk])


def _rows(*pairs):
    return [(label, value) for label, value in pairs if value not in (None, "", "-")]


def _academy_footer_note(site):
    return f"For anything urgent, please call us on {site.phone}." if site.phone else ""


# ---- admission enquiry -------------------------------------------------------------------------------------------------
def _enquiry_rows(obj):
    return _rows(
        ("Name", obj.applicant_name), ("Mobile", obj.mobile), ("Email", obj.email), ("City / area", obj.city),
        ("Date of birth", obj.date_of_birth.strftime("%d %b %Y") if obj.date_of_birth else ""),
        ("Parent / guardian", " ".join(x for x in (obj.guardian_name, obj.guardian_mobile) if x)),
        ("School / college", obj.institution),
        ("Program", str(obj.program) if obj.program else "General enquiry"),
        ("Type of shooting", obj.get_shooting_interest_display() if obj.shooting_interest else ""),
        ("Experience", obj.get_experience_level_display() if obj.experience_level else ""),
        ("Preferred time", obj.get_preferred_time_display() if obj.preferred_time else ""),
        ("Preferred contact", obj.get_preferred_contact_display()),
    )


def enquiry_received(obj):
    """Thank-you mail to the applicant."""
    ctx = _context(
        heading="Thank you for your enquiry", greeting=f"Namaste {obj.applicant_name},",
        paragraphs=["We have received your admission enquiry. Our team will get back to you shortly."],
        details=_rows(
            ("Program", str(obj.program) if obj.program else "General enquiry"),
            ("Type of shooting", obj.get_shooting_interest_display() if obj.shooting_interest else ""),
            ("Experience", obj.get_experience_level_display() if obj.experience_level else ""),
            ("We will contact you by", obj.get_preferred_contact_display()),
        ),
        button=("Visit our website", settings.SITE_URL), note=_academy_footer_note(SiteSettings.load()),
    )
    return _send("Thank you for your admission enquiry | Rudra Sports", [obj.email], ctx)


def enquiry_alert(obj):
    """Alert to the academy."""
    ctx = _context(
        heading="New admission enquiry", greeting="",
        paragraphs=[f"{obj.applicant_name} has sent an admission enquiry through the website."],
        details=_enquiry_rows(obj) + _rows(("Message", obj.message)),
        button=("Open in admin panel", _admin_url("admin:admissions_admissionenquiry_change", obj.pk)),
        note="Reply to this email to write to the applicant directly.",
    )
    return _staff(f"New admission enquiry: {obj.applicant_name}", ctx, reply_to=[obj.email])


# ---- contact form ------------------------------------------------------------------------------------------------------
def contact_received(obj):
    ctx = _context(
        heading="Thank you for contacting us", greeting=f"Namaste {obj.name},",
        paragraphs=["We have received your message. Our team will get back to you shortly."],
        details=_rows(("Subject", obj.subject), ("Your message", obj.message)),
        button=("Visit our website", settings.SITE_URL), note=_academy_footer_note(SiteSettings.load()),
    )
    return _send("We received your message | Rudra Sports", [obj.email], ctx)


def contact_alert(obj):
    ctx = _context(
        heading="New website message", greeting="",
        paragraphs=[f"{obj.name} has written to you through the contact form."],
        details=_rows(("Name", obj.name), ("Email", obj.email), ("Phone", obj.phone), ("Subject", obj.subject), ("Message", obj.message)),
        button=("Open in admin panel", _admin_url("admin:contact_contactmessage_change", obj.pk)),
        note="Reply to this email to write to the sender directly.",
    )
    return _staff(f"New website message: {obj.subject}", ctx, reply_to=[obj.email])


# ---- slot booking ------------------------------------------------------------------------------------------------------
def _slot_rows(b):
    slot = b.slot
    when = datetime.combine(slot.date, slot.start_time)
    until = datetime.combine(slot.date, slot.end_time)
    return _rows(
        ("Booking reference", b.reference),
        ("Date", when.strftime("%A, %d %B %Y")),
        ("Time", f"{when.strftime('%I:%M %p').lstrip('0')} to {until.strftime('%I:%M %p').lstrip('0')}"),
        ("Program", slot.program.title if slot.program else "Practice slot"),
        ("Seats", str(b.participants)),
        ("Type of shooting", b.get_shooting_type_display() if b.shooting_type else ""),
        ("Experience", b.get_experience_level_display() if b.experience_level else ""),
    )


def _address_rows(site):
    return _rows(("Address", site.address), ("Phone", site.phone), ("Range timing", site.opening_hours))


def booking_received(b):
    """'Request received' mail: only when the visitor left an email."""
    if not b.email:
        return False
    site = SiteSettings.load()
    ctx = _context(
        heading="We received your booking request", greeting=f"Namaste {b.name},",
        paragraphs=["Thank you for choosing Rudra Sports. Your slot request is with our team, and we will get back to you to confirm it. "
                    "Please keep your booking reference handy."],
        details=_slot_rows(b), button=("Visit our website", settings.SITE_URL), note=_academy_footer_note(site),
    )
    return _send(f"Booking request {b.reference} received | Rudra Sports", [b.email], ctx)


def booking_alert(b):
    ctx = _context(
        heading="New slot booking request", greeting="",
        paragraphs=[f"{b.name} has requested a slot through the website. It stays Pending until you confirm it."],
        details=_slot_rows(b) + _rows(("Name", b.name), ("Mobile", b.mobile), ("Email", b.email), ("Message", b.message)),
        button=("Review in admin panel", _admin_url("admin:bookings_slotbooking_change", b.pk)),
        note="Reply to this email to write to the visitor directly." if b.email else "",
    )
    return _staff(f"New slot booking {b.reference}: {b.name}", ctx, reply_to=[b.email] if b.email else None)


def booking_confirmed(b):
    if not b.email:
        return False
    site = SiteSettings.load()
    ctx = _context(
        heading="Your slot is confirmed", greeting=f"Namaste {b.name},",
        paragraphs=["Good news: your booking is confirmed. We look forward to seeing you at the range. Please bring this reference number with you."],
        details=_slot_rows(b) + _address_rows(site),
        button=("Get directions", site.directions_url), note=_academy_footer_note(site),
    )
    return _send(f"Booking {b.reference} confirmed | Rudra Sports", [b.email], ctx)


def booking_cancelled(b):
    if not b.email:
        return False
    site = SiteSettings.load()
    ctx = _context(
        heading="Your booking was cancelled", greeting=f"Namaste {b.name},",
        paragraphs=["Your slot booking has been cancelled and the seats have been released. "
                    "You are welcome to choose another slot whenever it suits you."],
        details=_slot_rows(b), button=("Book another slot", settings.SITE_URL.rstrip("/") + reverse("bookings:slots")),
        note=_academy_footer_note(site),
    )
    return _send(f"Booking {b.reference} cancelled | Rudra Sports", [b.email], ctx)
