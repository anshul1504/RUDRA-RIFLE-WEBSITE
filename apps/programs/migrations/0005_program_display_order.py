"""Client-requested display order: Beginner, Junior, Advanced Competitive Training, Pay and Play.

Only the `order` column of the four seeded programs is touched; names, prices/details, descriptions and booking flags are unchanged.
"""
from django.db import migrations

ORDER = [
    "beginner-shooting-program",
    "junior-shooter-development-program",
    "advanced-competitive-training",
    "pay-and-play",
]


def forward(apps, schema_editor):
    Program = apps.get_model("programs", "Program")
    for position, slug in enumerate(ORDER):
        Program.objects.filter(slug=slug).update(order=position)


class Migration(migrations.Migration):
    dependencies = [("programs", "0004_seed_pay_and_play")]
    operations = [migrations.RunPython(forward, migrations.RunPython.noop)]
