from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("api", "0018_flight_permit_purpose_list")]

    operations = [
        migrations.AddField(
            model_name="flightpermit",
            name="template_code",
            field=models.CharField(
                db_index=True,
                default="institution_a",
                max_length=64,
            ),
        ),
        migrations.AddField(
            model_name="flightpermit",
            name="template_data",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
