from django.db import migrations, models


def clear_non_a_recommendations(apps, schema_editor):
    FlightPermit = apps.get_model("api", "FlightPermit")
    FlightPermit.objects.exclude(template_code="institution_a").filter(
        is_recommendation=True
    ).update(is_recommendation=False)


class Migration(migrations.Migration):
    dependencies = [("api", "0019_flightpermit_templates")]

    operations = [
        migrations.RunPython(clear_non_a_recommendations, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="flightpermit",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(("template_code", "institution_a"))
                    | models.Q(("is_recommendation", False))
                ),
                name="flight_permit_recommendation_only_for_a",
            ),
        ),
    ]
