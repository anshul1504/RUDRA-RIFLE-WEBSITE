"""Set the academy's Google Maps location (22.7558407, 75.7659442) where no map has been configured yet."""
from django.db import migrations, models

LINK = "https://www.google.com/maps?q=22.7558407,75.7659442&z=17&hl=en"
EMBED = "https://maps.google.com/maps?q=22.7558407,75.7659442&z=17&hl=en&output=embed"


def set_map(apps, schema_editor):
    Site = apps.get_model("core", "SiteSettings")
    Site.objects.filter(map_embed_url="").update(map_embed_url=EMBED)
    Site.objects.filter(map_link_url="").update(map_link_url=LINK)


class Migration(migrations.Migration):
    dependencies = [("core", "0012_instagramreel")]
    operations = [
        migrations.AlterField(
            model_name="sitesettings", name="map_embed_url",
            field=models.URLField(blank=True, default=EMBED, max_length=1000,
                                  help_text="Google Maps embed URL used in the map frame (iframe src). Default: the academy's coordinates, no API key needed."),
        ),
        migrations.AlterField(
            model_name="sitesettings", name="map_link_url",
            field=models.URLField(blank=True, default=LINK, max_length=1000,
                                  help_text="Public Google Maps link behind 'Open in Google Maps' / 'Get directions'. If blank, a search link built from the address is used."),
        ),
        migrations.RunPython(set_map, migrations.RunPython.noop),
    ]
