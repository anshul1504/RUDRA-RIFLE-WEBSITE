"""Seed facilities (from the requirements document) and DRAFT legal pages."""
from django.db import migrations

FACILITIES = [
    ("Modern Shooting Range", "bi-bullseye", "A modern shooting range for rifle and pistol practice, as described by the academy."),
    ("Certified Coaches", "bi-patch-check", "Coaching by certified coaches, as stated by the academy."),
    ("Safe Training Environment", "bi-shield-lock", "Supervised sessions built around proper firearm handling and discipline protocols."),
    ("Professional Equipment", "bi-tools", "Professional equipment for training sessions."),
    ("Practice Sessions", "bi-calendar-check", "Guided practice sessions to build technique and consistency."),
    ("Competition Preparation", "bi-flag", "Preparation and guidance for district, state and national competitions."),
    ("Individual Attention for Every Shooter", "bi-person-check", "Attention to each shooter's progress, from beginner to competitive level."),
]

PRIVACY = """## Draft notice
DRAFT - This policy is a starting point written for Rudra Sports Rifle Shooting Society. It has not been reviewed by a legal adviser. The academy must review and confirm every statement below before relying on it.

## Who we are
Rudra Sports Rifle Shooting Society, Oxford International College, Opp. Pitra Parvat, Hatod Road, Gandhi Nagar, Indore, Madhya Pradesh. Email: rudrasportsrss@gmail.com. Phone: 94250 93128.

## Information we collect
When you use the admission enquiry or contact form on this website we collect only the details you type in:
- Name, and the parent or guardian's name where applicable
- Email address and mobile number
- Date of birth (optional on the admission form)
- Program of interest, preferred contact method and your message
- The time you gave consent

We do not ask for identity documents, medical information or payment details through this website.

## How we use it
- To reply to your enquiry and contact you in the way you prefer
- To manage admissions and follow up with you
- To keep a record of enquiries received

## Sharing
[TO BE CONFIRMED BY THE ACADEMY: state whether details are shared with any third party, such as a shooting federation or service provider.]

## Retention
[TO BE CONFIRMED BY THE ACADEMY: state how long enquiry records are kept.]

## Your choices
You may ask us to correct or delete the details you submitted by writing to rudrasportsrss@gmail.com.

## Cookies
This website uses only the cookies needed for security (such as form protection) and for the administration area. [TO BE CONFIRMED if analytics or other tools are added later.]

## Changes
We may update this policy. The date it was last reviewed will be shown on this page once confirmed.
"""

TERMS = """## Draft notice
DRAFT - These terms are a starting point written for the Rudra Sports Rifle Shooting Society website. They have not been reviewed by a legal adviser. The academy must review and confirm them before relying on them.

## About this website
This website provides information about Rudra Sports Rifle Shooting Society, Indore, Madhya Pradesh, including its training programs, facilities and events.

## Information on this website
We try to keep information accurate and up to date, but programs, facilities, schedules and events may change. Contact the academy to confirm details before making plans.

## Enquiries and admission
Submitting an enquiry form does not guarantee admission to any program. Admission, eligibility, fees and schedules are decided by the academy. [TO BE CONFIRMED BY THE ACADEMY.]

## Safety and responsible conduct
Shooting sports are practised only under supervision and in line with the academy's safety rules and applicable law. Visitors and trainees must follow instructions from the academy's staff. [TO BE CONFIRMED BY THE ACADEMY: add applicable licensing, age and safety requirements.]

## Acceptable use
You agree not to misuse this website, attempt to gain unauthorised access, or submit false or abusive information through its forms.

## Intellectual property
The name, logo, text and images on this website belong to Rudra Sports Rifle Shooting Society or its licensors and may not be reused without permission.

## Limitation of liability
[TO BE CONFIRMED BY A LEGAL ADVISER.]

## Governing law
[TO BE CONFIRMED BY THE ACADEMY: governing law and jurisdiction.]

## Contact
Rudra Sports Rifle Shooting Society, Oxford International College, Opp. Pitra Parvat, Hatod Road, Gandhi Nagar, Indore, Madhya Pradesh. Email: rudrasportsrss@gmail.com.
"""


def seed(apps, schema_editor):
    Facility = apps.get_model("core", "Facility")
    LegalPage = apps.get_model("core", "LegalPage")
    for i, (title, icon, desc) in enumerate(FACILITIES):
        Facility.objects.get_or_create(title=title, defaults={"icon": icon, "description": desc, "order": i})
    LegalPage.objects.get_or_create(slug="privacy-policy", defaults={"title": "Privacy Policy", "body": PRIVACY})
    LegalPage.objects.get_or_create(slug="terms-and-conditions", defaults={"title": "Website Terms and Conditions", "body": TERMS})


class Migration(migrations.Migration):
    dependencies = [("core", "0001_initial")]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
