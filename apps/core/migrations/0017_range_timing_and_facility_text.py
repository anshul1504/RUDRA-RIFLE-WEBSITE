"""Range timing (10 am - 5 pm daily, Friday closed) and updated facility wording."""
from django.db import migrations

HOURS = "10:00 am to 5:00 pm daily. Friday: Holiday."
FACILITY = {
    "Modern Shooting Range": (
        "A modern shooting range for rifle and pistol practice, as described by the academy.",
        "A modern range for rifle and pistol practice, open daily from 10:00 am to 5:00 pm (closed on Fridays).",
    ),
    "Certified Coaches": (
        "Coaching by certified coaches, as stated by the academy.",
        "Train yourself under certified ISSF / NRAI Coaches.",
    ),
}


def forwards(apps, schema_editor):
    Facility = apps.get_model("core", "Facility")
    for title, (old, new) in FACILITY.items():
        Facility.objects.filter(title=title, description=old).update(description=new)
    SiteSettings = apps.get_model("core", "SiteSettings")
    site, _ = SiteSettings.objects.get_or_create(pk=1)
    if not site.opening_hours:
        site.opening_hours = HOURS
        site.save(update_fields=["opening_hours"])


class Migration(migrations.Migration):
    dependencies = [("core", "0016_sitesettings_mission_text")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
