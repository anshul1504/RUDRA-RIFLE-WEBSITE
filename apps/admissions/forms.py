import re
from datetime import timedelta

from django import forms
from django.utils import timezone

from apps.core.utils import clean_text
from apps.programs.models import Program

from .models import AdmissionEnquiry

MOBILE_RE = re.compile(r"^[6-9]\d{9}$")


def normalise_mobile(raw):
    """Accept '94250 93128', '+91 94250-93128', '094250 93128' -> '9425093128'."""
    digits = re.sub(r"\D", "", raw or "")
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    elif len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]
    return digits


def age_on(dob, today):
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


class AdmissionEnquiryForm(forms.ModelForm):
    # Honeypot: real visitors never see or fill this field.
    contact_website = forms.CharField(required=False, widget=forms.TextInput(attrs={
        "tabindex": "-1", "autocomplete": "off", "aria-hidden": "true",
    }))

    consent = forms.BooleanField(
        required=True,
        label="I agree that Rudra Sports Rifle Shooting Society may store my details and contact me about this enquiry.",
        error_messages={"required": "Please tick the consent box so we can contact you."},
    )

    class Meta:
        model = AdmissionEnquiry
        fields = [
            "applicant_name", "date_of_birth", "gender", "city", "institution",
            "guardian_name", "guardian_mobile",
            "mobile", "email", "preferred_contact",
            "program", "shooting_interest", "experience_level", "preferred_time", "how_heard", "message", "consent",
        ]
        labels = {
            "applicant_name": "Applicant name",
            "date_of_birth": "Date of birth",
            "gender": "Gender",
            "city": "City / area",
            "institution": "School / college & class",
            "guardian_name": "Parent / guardian name",
            "guardian_mobile": "Parent / guardian mobile",
            "mobile": "Mobile number",
            "email": "Email address",
            "preferred_contact": "Preferred contact method",
            "program": "Program of interest",
            "shooting_interest": "Type of shooting",
            "experience_level": "Previous shooting experience",
            "preferred_time": "Preferred training time",
            "how_heard": "How did you hear about us?",
            "message": "Anything else you would like us to know?",
        }
        help_texts = {
            "date_of_birth": "Used to suggest the right program. Applicants under 18 need a parent / guardian.",
            "gender": "Optional.",
            "institution": "Optional. For students, e.g. Oxford International College, Class 9.",
            "guardian_name": "Required if the applicant is under 18.",
            "guardian_mobile": "Required if the applicant is under 18. 10-digit Indian mobile number.",
            "mobile": "10-digit Indian mobile number.",
            "preferred_time": "Optional. Batch timings are confirmed by the academy.",
            "how_heard": "Optional.",
            "message": "Optional. Questions, goals or anything that helps us advise you.",
        }
        widgets = {
            "applicant_name": forms.TextInput(attrs={"autocomplete": "name"}),
            "date_of_birth": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "city": forms.TextInput(attrs={"autocomplete": "address-level2"}),
            "institution": forms.TextInput(attrs={"autocomplete": "organization"}),
            "guardian_name": forms.TextInput(attrs={"autocomplete": "off"}),
            "guardian_mobile": forms.TextInput(attrs={"autocomplete": "off", "inputmode": "tel", "placeholder": "e.g. 98765 43210"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "mobile": forms.TextInput(attrs={"autocomplete": "tel", "inputmode": "tel", "placeholder": "e.g. 98765 43210"}),
            "message": forms.Textarea(attrs={"rows": 4}),
        }

    SELECTS = {"gender": "Select (optional)", "shooting_interest": "Select the type of shooting",
               "experience_level": "Select your experience", "preferred_time": "Select (optional)", "how_heard": "Select (optional)"}
    REQUIRED = {
        "applicant_name": "Please enter the applicant's full name.",
        "date_of_birth": "Please enter the date of birth.",
        "city": "Please enter your city or area.",
        "mobile": "Please enter a mobile number.",
        "email": "Please enter an email address.",
        "shooting_interest": "Please choose the type of shooting.",
        "experience_level": "Please choose your previous shooting experience.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["program"].queryset = Program.objects.filter(is_published=True)
        self.fields["program"].empty_label = "Not sure yet / general enquiry"
        self.fields["program"].required = False
        for name, message in self.REQUIRED.items():
            self.fields[name].required = True
            self.fields[name].error_messages["required"] = message
        for name, prompt in self.SELECTS.items():
            field = self.fields[name]
            field.choices = [("", prompt)] + [c for c in field.choices if c[0] != ""]
            field.error_messages["invalid_choice"] = "Choose one of the available options."
        for name, field in self.fields.items():
            if name == "consent":
                field.widget.attrs["class"] = "form-check-input"
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "form-select"
            elif name != "contact_website":
                field.widget.attrs["class"] = "form-control"

    def clean_applicant_name(self):
        name = clean_text(self.cleaned_data["applicant_name"])
        if len(name) < 2:
            raise forms.ValidationError("Please enter the applicant's full name.")
        return name

    def clean_city(self):
        return clean_text(self.cleaned_data.get("city", ""))

    def clean_institution(self):
        return clean_text(self.cleaned_data.get("institution", ""))

    def clean_guardian_name(self):
        return clean_text(self.cleaned_data.get("guardian_name", ""))

    def clean_message(self):
        return clean_text(self.cleaned_data.get("message", ""))

    def clean_mobile(self):
        mobile = normalise_mobile(self.cleaned_data["mobile"])
        if not MOBILE_RE.match(mobile):
            raise forms.ValidationError("Enter a valid 10-digit Indian mobile number.")
        return mobile

    def clean_guardian_mobile(self):
        raw = self.cleaned_data.get("guardian_mobile", "")
        if not raw.strip():
            return ""
        mobile = normalise_mobile(raw)
        if not MOBILE_RE.match(mobile):
            raise forms.ValidationError("Enter a valid 10-digit Indian mobile number.")
        return mobile

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get("date_of_birth")
        if dob:
            today = timezone.localdate()
            if dob >= today:
                raise forms.ValidationError("Date of birth must be in the past.")
            if dob.year < today.year - 100:
                raise forms.ValidationError("Please check the date of birth.")
        return dob

    def clean_contact_website(self):
        if self.cleaned_data.get("contact_website"):
            raise forms.ValidationError("Spam detected.")
        return ""

    def clean(self):
        data = super().clean()
        dob = data.get("date_of_birth")
        if dob and age_on(dob, timezone.localdate()) < 18:
            if not data.get("guardian_name"):
                self.add_error("guardian_name", "Please enter a parent or guardian name for applicants under 18.")
            if not data.get("guardian_mobile") and "guardian_mobile" not in self.errors:
                self.add_error("guardian_mobile", "Please enter a parent or guardian mobile number for applicants under 18.")
        email, mobile = data.get("email"), data.get("mobile")
        if email and mobile and not self.errors:
            since = timezone.now() - timedelta(hours=24)
            if AdmissionEnquiry.objects.filter(email=email, mobile=mobile, created_at__gte=since).exists():
                raise forms.ValidationError(
                    "We have already received an enquiry with these details in the last 24 hours. "
                    "Our team will get in touch with you soon."
                )
        return data

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.consent_at = timezone.now()
        if commit:
            obj.save()
        return obj
