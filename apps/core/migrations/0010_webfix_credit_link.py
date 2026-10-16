from django.db import migrations, models


def set_link(apps, schema_editor):
    apps.get_model("core", "SiteSettings").objects.filter(developer_credit_url="").update(developer_credit_url="https://thewebfix.in")


class Migration(migrations.Migration):
    dependencies = [("core", "0009_more_facilities")]
    operations = [
        migrations.AlterField(
            model_name="sitesettings", name="developer_credit_url",
            field=models.URLField(blank=True, default="https://thewebfix.in", help_text="Where the credit links to.", verbose_name="Developer credit link"),
        ),
        migrations.RunPython(set_link, migrations.RunPython.noop),
    ]
