from django import forms
from django.db import transaction

from apps.admissions.forms import MOBILE_RE, normalise_mobile
from apps.core.utils import clean_text

from .models import ACTIVE_STATUSES, Slot, SlotBooking


class SlotBookingForm(forms.ModelForm):
    contact_website = forms.CharField(required=False, widget=forms.TextInput(attrs={
        "tabindex": "-1", "autocomplete": "off", "aria-hidden": "true",
    }))
    consent = forms.BooleanField(
        required=True,
        label="I agree that Rudra Sports Rifle Shooting Society may store my details and contact me about this booking.",
        error_messages={"required": "Please tick the consent box so we can confirm your booking."},
    )

    class Meta:
        model = SlotBooking
        fields = ["name", "mobile", "email", "participants", "experience_level", "shooting_type", "message", "consent"]
        labels = {"name": "Your name", "mobile": "Mobile number", "email": "Email address (optional)",
                  "participants": "Number of shooters", "message": "Note (optional)",
                  "experience_level": "Previous Shooting Experience", "shooting_type": "Type of Shooting"}
        help_texts = {"mobile": "10-digit Indian mobile number. We confirm your slot on this number."}
        widgets = {
            "name": forms.TextInput(attrs={"autocomplete": "name"}),
            "mobile": forms.TextInput(attrs={"autocomplete": "tel", "inputmode": "tel"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "participants": forms.NumberInput(attrs={"min": 1, "max": 20}),
            "message": forms.TextInput(),
            "experience_level": forms.Select(),
            "shooting_type": forms.Select(),
        }

    def __init__(self, *args, slot, **kwargs):
        super().__init__(*args, **kwargs)
        self.slot = slot
        # Both choices are mandatory: replace the model's blank "---------" option with a clear prompt and validate server-side.
        for name, prompt, error in [
            ("experience_level", "Select your experience", "Please choose your previous shooting experience."),
            ("shooting_type", "Select the type of shooting", "Please choose the type of shooting."),
        ]:
            field = self.fields[name]
            field.required = True
            field.choices = [("", prompt)] + [c for c in field.choices if c[0] != ""]
            field.error_messages["required"] = error
            field.error_messages["invalid_choice"] = "Choose one of the available options."
        for name, field in self.fields.items():
            if name == "consent":
                field.widget.attrs["class"] = "form-check-input"
            elif name in ("experience_level", "shooting_type"):
                field.widget.attrs["class"] = "form-select"
            elif name != "contact_website":
                field.widget.attrs["class"] = "form-control"

    def clean_name(self):
        name = clean_text(self.cleaned_data["name"])
        if len(name) < 2:
            raise forms.ValidationError("Please enter your name.")
        return name

    def clean_message(self):
        return clean_text(self.cleaned_data.get("message", ""))

    def clean_email(self):
        return self.cleaned_data.get("email", "").strip().lower()

    def clean_mobile(self):
        mobile = normalise_mobile(self.cleaned_data["mobile"])
        if not MOBILE_RE.match(mobile):
            raise forms.ValidationError("Enter a valid 10-digit Indian mobile number.")
        return mobile

    def clean_contact_website(self):
        if self.cleaned_data.get("contact_website"):
            raise forms.ValidationError("Spam detected.")
        return ""

    def clean(self):
        data = super().clean()
        mobile = data.get("mobile")
        if mobile and not self.errors:
            if SlotBooking.objects.filter(slot=self.slot, mobile=mobile, status__in=ACTIVE_STATUSES).exists():
                raise forms.ValidationError("A booking for this slot already exists with this mobile number.")
        return data

    def save(self, commit=True):
        """Create the booking only if seats are still free (checked under a row lock)."""
        with transaction.atomic():
            slot = Slot.objects.select_for_update().get(pk=self.slot.pk)
            if not slot.is_published or slot.is_past:
                raise forms.ValidationError("Sorry, this slot is no longer open for booking.")
            wanted = self.cleaned_data["participants"]
            if wanted > slot.seats_left:
                raise SeatsUnavailable(slot.seats_left)
            booking = super().save(commit=False)
            booking.slot = slot
            booking.save()
            return booking


class SeatsUnavailable(Exception):
    def __init__(self, left):
        self.left = left
        super().__init__(f"Only {left} seat(s) left")
