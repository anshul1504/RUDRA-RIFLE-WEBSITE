from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("core", "0010_webfix_credit_link")]
    operations = [
        migrations.RemoveField(model_name="sitesettings", name="developer_credit_text"),
        migrations.RemoveField(model_name="sitesettings", name="developer_credit_url"),
    ]
