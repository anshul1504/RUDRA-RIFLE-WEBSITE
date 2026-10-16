"""Switch to rudrasports.com addresses and seed the homepage carousel slides."""
from django.db import migrations

OLD = "rudrasportsrss@gmail.com"
NEW = "info@rudrasports.com"

SLIDES = [
    {"eyebrow": "Indore, Madhya Pradesh", "headline": "Train Like a", "headline_accent": "Champion.",
     "text": "Professional Rifle & Pistol Shooting Training for Beginners and Competitive Shooters.",
     "primary_label": "Enquire for Admission", "primary_link": "/admission/",
     "secondary_label": "Explore Training Programs", "secondary_link": "/programs/"},
    {"eyebrow": "Beginner Shooting Program", "headline": "Learn the basics,", "headline_accent": "the safe way.",
     "text": "Safety training, aiming techniques, trigger control, posture and breathing, under guided supervision.",
     "primary_label": "View the program", "primary_link": "/programs/beginner-shooting-program/",
     "secondary_label": "Enquire now", "secondary_link": "/admission/"},
    {"eyebrow": "Pay and Play", "headline": "Book your", "headline_accent": "practice slot.",
     "text": "Choose an available slot online and send a booking request. The academy confirms it with you.",
     "primary_label": "Book a slot", "primary_link": "/book/",
     "secondary_label": "How it works", "secondary_link": "/programs/pay-and-play/"},
    {"eyebrow": "Junior Shooter Development", "headline": "Build discipline", "headline_accent": "from an early age.",
     "text": "Specially designed for school and college students to develop shooting skills and discipline.",
     "primary_label": "Explore the program", "primary_link": "/programs/junior-shooter-development-program/",
     "secondary_label": "Contact us", "secondary_link": "/contact/"},
]


def forward(apps, schema_editor):
    Site = apps.get_model("core", "SiteSettings")
    Site.objects.filter(email=OLD).update(email=NEW)
    Legal = apps.get_model("core", "LegalPage")
    for page in Legal.objects.filter(body__contains=OLD):
        page.body = page.body.replace(OLD, NEW)
        page.save(update_fields=["body"])
    Slide = apps.get_model("core", "HeroSlide")
    if not Slide.objects.exists():
        for i, data in enumerate(SLIDES):
            Slide.objects.create(order=i, **data)


class Migration(migrations.Migration):
    dependencies = [("core", "0005_heroslide_sitesettings_contact_email_and_more")]
    operations = [migrations.RunPython(forward, migrations.RunPython.noop)]
