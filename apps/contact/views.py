import logging

from django.contrib import messages
from django.shortcuts import redirect, render

from apps.core.models import Faq
from apps.core.utils import acknowledge, notify_staff, throttled

from .forms import ContactForm

logger = logging.getLogger(__name__)


def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if throttled(request, "contact"):
            messages.error(request, "Too many messages from your connection. Please wait a few minutes and try again, or call us.")
        elif form.is_valid():
            obj = form.save()
            logger.info("Contact message %s received", obj.pk)
            notify_staff(
                f"New website message: {obj.subject}",
                f"From: {obj.name} <{obj.email}> {obj.phone}\n\n{obj.message}",
            )
            acknowledge(obj.email, "We received your message", obj.name,
                        "Thank you for writing to us. We will reply as soon as we can.")
            request.session["contact_submitted"] = True
            return redirect("contact:thanks")
        else:
            messages.error(request, "Please correct the highlighted fields and send again.")
    else:
        form = ContactForm()
    return render(request, "contact/contact.html", {
        "form": form,
        "faqs": Faq.objects.filter(is_published=True),
        "meta_description": "Contact Rudra Sports Rifle Shooting Society, Hatod Road, Indore: phone, email, WhatsApp and location.",
    })


def thanks(request):
    if not request.session.pop("contact_submitted", False):
        return redirect("contact:contact")
    return render(request, "contact/thanks.html", {"meta_robots": "noindex"})
