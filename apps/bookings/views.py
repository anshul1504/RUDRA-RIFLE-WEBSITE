import logging
from itertools import groupby

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render

from apps.core.utils import acknowledge, notify_staff, page_enabled, paginate, throttled

from .forms import SeatsUnavailable, SlotBookingForm
from .models import Slot, SlotBooking

logger = logging.getLogger(__name__)


@page_enabled("show_booking")
def slot_list(request):
    slots = list(Slot.objects.open_for_booking().with_booked())
    slots = [s for s in slots if not s.is_past]
    all_days = [{"date": d, "slots": list(items)} for d, items in groupby(slots, key=lambda s: s.date)]
    page = paginate(request, all_days, 7)  # one page = one week of dates
    return render(request, "bookings/slot_list.html", {
        "page_obj": page,
        "days": page.object_list,
        "meta_description": "Book a Pay and Play practice slot at Rudra Sports Rifle Shooting Society, Indore.",
    })


@page_enabled("show_booking")
def book_slot(request, pk):
    slot = get_object_or_404(Slot.objects.open_for_booking().with_booked(), pk=pk)
    if slot.is_past:
        messages.error(request, "That slot has already started. Please choose another one.")
        return redirect("bookings:slots")
    if request.method == "POST":
        form = SlotBookingForm(request.POST, slot=slot)
        if throttled(request, "booking"):
            messages.error(request, "Too many requests from your connection. Please wait a few minutes or call us.")
        elif form.is_valid():
            try:
                booking = form.save()
            except SeatsUnavailable as exc:
                form.add_error("participants", f"Only {exc.left} seat(s) left in this slot." if exc.left else "This slot is now full.")
            except ValidationError as exc:
                form.add_error(None, exc)
            else:
                logger.info("Slot booking %s received", booking.reference)
                notify_staff(
                    f"New slot booking {booking.reference}: {booking.name}",
                    f"{booking.name} ({booking.mobile}) booked {booking.participants} seat(s) for {slot}.\n"
                    f"Type: {booking.get_shooting_type_display()}\nExperience: {booking.get_experience_level_display()}",
                )
                acknowledge(booking.email, f"Booking request {booking.reference}", booking.name,
                            f"We received your booking request for {slot}. Reference: {booking.reference}. The academy will confirm your slot with you.")
                request.session["booking_ref"] = booking.reference
                return redirect("bookings:confirmation", reference=booking.reference)
            messages.error(request, "We could not complete the booking. Please check the details below.")
        else:
            messages.error(request, "Please correct the highlighted fields and submit again.")
    else:
        form = SlotBookingForm(slot=slot)
    return render(request, "bookings/book.html", {"form": form, "slot": slot, "meta_robots": "noindex"})


@page_enabled("show_booking")
def confirmation(request, reference):
    if request.session.get("booking_ref") != reference:
        return redirect("bookings:slots")
    booking = get_object_or_404(SlotBooking.objects.select_related("slot", "slot__program"), reference=reference)
    return render(request, "bookings/confirmation.html", {"booking": booking, "meta_robots": "noindex"})
