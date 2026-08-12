import json

from django.db import migrations, models


LEGACY_PURPOSE_CODES = {
    "Test Uçuşu": "production_flight_test",
    "İntikal Uçuşu": "ferry_repositioning",
}


def convert_purposes_to_lists(apps, schema_editor):
    FlightPermit = apps.get_model("api", "FlightPermit")
    for permit in FlightPermit.objects.all().iterator():
        legacy_value = (permit.purpose_of_flight or "").strip()
        purpose_code = LEGACY_PURPOSE_CODES.get(legacy_value)
        permit.purpose_of_flight = json.dumps([purpose_code] if purpose_code else [])
        if legacy_value and not purpose_code:
            legacy_note = f"[Eski kayıt] Uçuş amacı: {legacy_value}"
            permit.notes = f"{permit.notes.rstrip()}\n{legacy_note}".lstrip()
        permit.save(update_fields=["purpose_of_flight", "notes"])


class Migration(migrations.Migration):
    dependencies = [("api", "0017_update_flight_permit_fields")]

    operations = [
        migrations.RunPython(convert_purposes_to_lists, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="flightpermit",
            name="purpose_of_flight",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
