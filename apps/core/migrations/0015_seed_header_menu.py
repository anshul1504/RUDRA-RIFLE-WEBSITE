"""Create the header menu items. Everything is visible except Achievements, which is hidden for now (client request).

Hiding is purely a visibility flag: the Achievements page, its content and URL are untouched, and it can be switched
back on in Admin > Header menu.
"""
from django.db import migrations

ITEMS = [
    ("home", "Home", "core:home", False, True),
    ("about", "About Us", "core:about", False, True),
    ("programs", "Training Programs", "programs:list", False, True),
    ("facilities", "Facilities", "core:facilities", False, True),
    ("gallery", "Gallery", "gallery:index", False, True),
    ("achievements", "Achievements", "achievements:list", False, False),  # hidden by default
    ("events", "Events", "events:list", False, True),
    ("contact", "Contact", "contact:contact", False, True),
    ("enquiry", "Admission Enquiry", "admissions:enquiry", True, True),
]


def seed(apps, schema_editor):
    MenuItem = apps.get_model("core", "MenuItem")
    for order, (key, label, url_name, is_cta, visible) in enumerate(ITEMS):
        # get_or_create: never overwrites a visibility choice that already exists
        MenuItem.objects.get_or_create(key=key, defaults={"label": label, "url_name": url_name, "is_cta": is_cta, "order": order, "is_visible": visible})


class Migration(migrations.Migration):
    dependencies = [("core", "0014_menuitem")]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
