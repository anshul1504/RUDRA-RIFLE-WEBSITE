"""Modern Shooting Range card: the academy's own training statement."""
from django.db import migrations

OLD = (
    "A modern shooting range for rifle and pistol practice, as described by the academy.",
    "A modern range for rifle and pistol practice, open daily from 10:00 am to 5:00 pm (closed on Fridays).",
)
NEW = ("Our training focuses on safety, discipline, accuracy, focus, and sportsmanship, "
       "with structured practice sessions designed to help every shooter reach their full potential.")


def forwards(apps, schema_editor):
    apps.get_model("core", "Facility").objects.filter(title="Modern Shooting Range", description__in=OLD).update(description=NEW)


class Migration(migrations.Migration):
    dependencies = [("core", "0017_range_timing_and_facility_text")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
