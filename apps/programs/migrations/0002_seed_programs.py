"""Initial programs, taken verbatim in meaning from the academy's requirements document.

Fees, timings, eligibility and duration are intentionally left blank: they are
shown on the site only after the academy supplies them in Django Admin.
"""
from django.db import migrations

PROGRAMS = [
    {
        "title": "Beginner Shooting Program",
        "slug": "beginner-shooting-program",
        "icon": "bi-bullseye",
        "summary": "Perfect for students and newcomers who want to learn the basics of rifle and pistol shooting.",
        "description": (
            "Perfect for students and newcomers who want to learn the basics of rifle and pistol shooting.\n\n"
            "Training is conducted under safe and guided supervision, starting with safety and building up "
            "the fundamentals step by step."
        ),
        "highlights": ["Safety training", "Basic aiming techniques", "Trigger control", "Shooting posture", "Breathing techniques"],
    },
    {
        "title": "Advanced Competitive Training",
        "slug": "advanced-competitive-training",
        "icon": "bi-trophy",
        "summary": "Designed for shooters preparing for competitions and championships.",
        "description": (
            "Designed for shooters preparing for competitions and championships.\n\n"
            "The program focuses on precision, mental strength and preparation for district, state and national "
            "level competition."
        ),
        "highlights": ["Match practice sessions", "Precision shooting drills", "Mental focus training", "Competition guidance", "Performance analysis"],
    },
    {
        "title": "Junior Shooter Development Program",
        "slug": "junior-shooter-development-program",
        "icon": "bi-people",
        "summary": "Specially designed for school and college students to develop shooting skills from an early stage.",
        "description": (
            "Specially designed for school and college students to develop shooting skills from an early stage.\n\n"
            "The program develops shooting fundamentals and discipline in young shooters under safe supervision."
        ),
        "highlights": ["Training for school and college students", "Development of shooting fundamentals and discipline"],
    },
]


def seed(apps, schema_editor):
    Program = apps.get_model("programs", "Program")
    Highlight = apps.get_model("programs", "ProgramHighlight")
    for i, data in enumerate(PROGRAMS):
        highlights = data.pop("highlights")
        program, created = Program.objects.get_or_create(slug=data["slug"], defaults={**data, "order": i, "is_published": True})
        if created:
            for j, text in enumerate(highlights):
                Highlight.objects.create(program=program, text=text, order=j)


class Migration(migrations.Migration):
    dependencies = [("programs", "0001_initial")]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
