from datetime import timedelta

from django import forms
from django.utils import timezone

from apps.admissions.forms import MOBILE_RE, normalise_mobile
from apps.core.utils import clean_text

from .models import ContactMessage


class ContactForm(forms.ModelForm):
    contact_website = forms.CharField(required=False, widget=forms.TextInput(attrs={
        "tabindex": "-1", "autocomplete": "off", "aria-hidden": "true",
    }))
    consent = forms.BooleanField(
        required=True,
        label="I agree that Rudra Sports Rifle Shooting Society may store my details and reply to this message.",
        error_messages={"required": "Please tick the consent box so we can reply to you."},
    )

    class Meta:
        model = ContactMessage
        fields = ["name", "email", "phone", "subject", "message", "consent"]
        labels = {"name": "Your name", "email": "Email address", "phone": "Mobile number (optional)"}
        widgets = {
            "name": forms.TextInput(attrs={"autocomplete": "name"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "phone": forms.TextInput(attrs={"autocomplete": "tel", "inputmode": "tel"}),
            "message": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name == "consent":
                field.widget.attrs["class"] = "form-check-input"
            elif name != "contact_website":
                field.widget.attrs["class"] = "form-control"

    def clean_name(self):
        name = clean_text(self.cleaned_data["name"])
        if len(name) < 2:
            raise forms.ValidationError("Please enter your name.")
        return name

    def clean_subject(self):
        return clean_text(self.cleaned_data["subject"])

    def clean_message(self):
        message = clean_text(self.cleaned_data["message"])
        if len(message) < 10:
            raise forms.ValidationError("Please write a little more so we can help (at least 10 characters).")
        return message

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def clean_phone(self):
        raw = self.cleaned_data.get("phone", "")
        if not raw.strip():
            return ""
        phone = normalise_mobile(raw)
        if not MOBILE_RE.match(phone):
            raise forms.ValidationError("Enter a valid 10-digit Indian mobile number, or leave this blank.")
        return phone

    def clean_contact_website(self):
        if self.cleaned_data.get("contact_website"):
            raise forms.ValidationError("Spam detected.")
        return ""

    def clean(self):
        data = super().clean()
        email, message = data.get("email"), data.get("message")
        if email and message and not self.errors:
            since = timezone.now() - timedelta(hours=24)
            if ContactMessage.objects.filter(email=email, message=message, created_at__gte=since).exists():
                raise forms.ValidationError("We have already received this message. Thank you - we will reply soon.")
        return data
