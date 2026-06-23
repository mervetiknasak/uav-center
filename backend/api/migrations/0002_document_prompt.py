from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="document",
            name="prompt",
            field=models.TextField(blank=True),
        ),
    ]
