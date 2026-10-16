"""Bring the facilities list to 12 cards. The new entries come straight from the training items in the academy document."""
from django.db import migrations

NEW = [
    ("Safety Training & Protocols", "bi-shield-check", "Every trainee is guided through proper firearm handling and discipline protocols."),
    ("Basic Aiming & Trigger Control", "bi-crosshair", "Foundations of aiming, trigger control, posture and breathing for new shooters."),
    ("Mental Focus Training", "bi-bullseye", "Concentration and mental strength built alongside technique."),
    ("Performance Analysis", "bi-graph-up-arrow", "Review of a shooter's progress to guide the next stage of training."),
    ("Competition Guidance", "bi-flag", "Guidance and support for district, state and national competitions."),
]


def seed(apps, schema_editor):
    Facility = apps.get_model("core", "Facility")
    start = Facility.objects.count()
    for i, (title, icon, desc) in enumerate(NEW):
        Facility.objects.get_or_create(title=title, defaults={"icon": icon, "description": desc, "order": start + i})


class Migration(migrations.Migration):
    dependencies = [("core", "0008_remove_sitesettings_contact_email_and_more")]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
