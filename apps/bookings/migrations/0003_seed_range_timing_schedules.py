"""Weekly pattern: hourly slots 10:00 am - 5:00 pm every day except Friday (holiday)."""
from datetime import time

from django.db import migrations

CAPACITY = 6  # editable per schedule in Django Admin


def forwards(apps, schema_editor):
    SlotSchedule = apps.get_model("bookings", "SlotSchedule")
    if SlotSchedule.objects.exists():
        return
    for weekday in (0, 1, 2, 3, 5, 6):  # Friday (4) is a holiday
        for hour in range(10, 17):
            SlotSchedule.objects.create(
                weekday=weekday, start_time=time(hour), end_time=time(hour + 1), capacity=CAPACITY, is_active=True,
            )


class Migration(migrations.Migration):
    dependencies = [("bookings", "0002_slotbooking_experience_level_and_more")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
