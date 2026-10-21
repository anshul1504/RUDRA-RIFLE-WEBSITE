import logging

from django.contrib import messages
from django.shortcuts import redirect, render

from apps.core.models import Faq
from apps.core import emails
from apps.core.utils import throttled
from apps.programs.models import Program

from .forms import AdmissionEnquiryForm

logger = logging.getLogger(__name__)


def enquiry(request):
    if request.method == "POST":
        form = AdmissionEnquiryForm(request.POST)
        if throttled(request, "admission"):
            messages.error(request, "Too many submissions from your connection. Please wait a few minutes and try again, or call us.")
        elif form.is_valid():
            obj = form.save()
            logger.info("Admission enquiry %s received", obj.pk)
            emails.enquiry_alert(obj)
            emails.enquiry_received(obj)
            request.session["admission_submitted"] = True
            return redirect("admissions:thanks")
        else:
            messages.error(request, "Please correct the highlighted fields and submit again.")
    else:
        initial = {}
        slug = request.GET.get("program")
        if slug:
            program = Program.objects.filter(slug=slug, is_published=True).first()
            if program:
                initial["program"] = program.pk
        form = AdmissionEnquiryForm(initial=initial)
    return render(request, "admissions/enquiry.html", {
        "form": form,
        "faqs": Faq.objects.filter(is_published=True),
        "meta_description": "Send an admission enquiry to Rudra Sports Rifle Shooting Society, Indore for rifle and pistol shooting training.",
    })


def thanks(request):
    if not request.session.pop("admission_submitted", False):
        return redirect("admissions:enquiry")
    return render(request, "admissions/thanks.html", {"meta_robots": "noindex"})
