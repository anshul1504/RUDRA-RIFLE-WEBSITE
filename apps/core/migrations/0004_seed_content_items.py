"""Move the document-sourced list content (mission, values, why choose us, focus areas) into the database
so it can be edited in Django Admin."""
from django.db import migrations

MISSION = [
    "Promote shooting sports among youth",
    "Provide professional rifle & pistol shooting training",
    "Develop discipline, concentration and self-confidence",
    "Prepare athletes for district, state and national competitions",
    "Encourage fitness, mental strength and sports ethics",
]
VALUES = [
    ("Discipline", "bi-compass", "Structured, supervised practice that builds routine and respect for the range."),
    ("Focus", "bi-bullseye", "Concentration and mental strength developed alongside technique."),
    ("Confidence", "bi-shield-check", "Self-belief that grows as every shooter progresses at their own level."),
    ("Sportsmanship", "bi-trophy", "Sports ethics and responsible conduct, on and off the range."),
]
WHY = [
    ("Experienced Trainers", "bi-person-badge"),
    ("Safe & Disciplined Environment", "bi-shield-lock"),
    ("Professional Coaching Methods", "bi-clipboard-check"),
    ("Focus on Mental Strength & Precision", "bi-bullseye"),
    ("Training for All Age Groups", "bi-people"),
    ("Support for Tournament Participation", "bi-flag"),
]
FOCUS = [
    ("Championship participation", "bi-flag", "Participation in district and state-level championships."),
    ("Aspiring national shooters", "bi-stars", "Training aspiring national shooters."),
    ("Youth engagement", "bi-people", "Promoting youth engagement in sports activities."),
    ("Confidence & discipline", "bi-shield-check", "Building confidence and discipline through shooting sports."),
]


def seed(apps, schema_editor):
    Item = apps.get_model("core", "ContentItem")
    if Item.objects.exists():
        return
    for i, t in enumerate(MISSION):
        Item.objects.create(kind="mission", title=t, icon="bi-check2-circle", order=i)
    for i, (t, icon, text) in enumerate(VALUES):
        Item.objects.create(kind="value", title=t, icon=icon, text=text, order=i)
    for i, (t, icon) in enumerate(WHY):
        Item.objects.create(kind="why", title=t, icon=icon, order=i)
    for i, (t, icon, text) in enumerate(FOCUS):
        Item.objects.create(kind="focus", title=t, icon=icon, text=text, order=i)


class Migration(migrations.Migration):
    dependencies = [("core", "0003_contentitem_facility_image_facility_image_alt_and_more")]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
