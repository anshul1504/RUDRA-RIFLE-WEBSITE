from django.db import migrations

CATEGORIES = [("Training", "training"), ("Range & Facilities", "range-facilities"), ("Events", "events"), ("Shooters", "shooters")]


def seed(apps, schema_editor):
    Category = apps.get_model("gallery", "Category")
    for i, (name, slug) in enumerate(CATEGORIES):
        Category.objects.get_or_create(slug=slug, defaults={"name": name, "order": i})


class Migration(migrations.Migration):
    dependencies = [("gallery", "0001_initial")]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
