"""Pay and Play photo is a tall portrait: anchor the crop at the top so the shooter's face stays visible."""
from django.db import migrations


def forward(apps, schema_editor):
    apps.get_model("programs", "Program").objects.filter(slug="pay-and-play").update(image_focus="top")


class Migration(migrations.Migration):
    dependencies = [("programs", "0006_program_image_focus")]
    operations = [migrations.RunPython(forward, migrations.RunPython.noop)]
