"""Add the 'Pay and Play' program. Wording is deliberately minimal and fully editable in Admin;
fees, timings and eligibility are left blank until the academy supplies them."""
from django.db import migrations


def seed(apps, schema_editor):
    Program = apps.get_model("programs", "Program")
    Highlight = apps.get_model("programs", "ProgramHighlight")
    program, created = Program.objects.get_or_create(
        slug="pay-and-play",
        defaults={
            "title": "Pay and Play",
            "icon": "bi-calendar2-check",
            "summary": "Book a practice slot at the range and pay for the session you use.",
            "description": (
                "Pay and Play lets you book individual practice slots at the range, with sessions supervised "
                "by the academy.\n\n"
                "Choose an available slot online and send a booking request. The academy will confirm your slot "
                "and share the session rates and any other details."
            ),
            "allow_booking": True,
            "order": 3,
            "is_published": True,
        },
    )
    if created:
        for i, text in enumerate([
            "Pay-per-session range practice",
            "Book your slot online",
            "Supervised, safety-first sessions",
        ]):
            Highlight.objects.create(program=program, text=text, order=i)


class Migration(migrations.Migration):
    dependencies = [("programs", "0003_program_allow_booking")]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
