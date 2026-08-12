from django.db import migrations, models


def migrate_legacy_flight_permits(apps, schema_editor):
    FlightPermit = apps.get_model("api", "FlightPermit")
    permit_type_labels = {
        "domestic": "Yurt İçi",
        "international": "Uluslararası",
        "test": "Test Uçuşu",
        "ferry": "İntikal Uçuşu",
    }
    for permit in FlightPermit.objects.all().iterator():
        permit.permit_applicant = "Belirtilmedi"
        permit.aircraft_id_mark = permit.aircraft_number
        permit.purpose_of_flight = permit_type_labels.get(permit.permit_type, permit.permit_type)
        permit.conditions_restrictions = permit.flight_region
        if permit.issuing_authority:
            legacy_authority = f"[Eski kayıt] İzni veren kurum: {permit.issuing_authority}"
            permit.notes = f"{permit.notes.rstrip()}\n{legacy_authority}".lstrip()
        permit.save(
            update_fields=[
                "permit_applicant",
                "aircraft_id_mark",
                "purpose_of_flight",
                "conditions_restrictions",
                "notes",
            ]
        )


class Migration(migrations.Migration):
    dependencies = [("api", "0016_notification_unknown_status")]

    operations = [
        migrations.AddField(
            model_name="flightpermit",
            name="permit_applicant",
            field=models.TextField(default="Belirtilmedi"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="flightpermit",
            name="aircraft_nationality",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="flightpermit",
            name="aircraft_id_mark",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="flightpermit",
            name="aircraft_owner",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="flightpermit",
            name="aircraft_type",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="flightpermit",
            name="aircraft_manufacturer",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="flightpermit",
            name="serial_number",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="flightpermit",
            name="purpose_of_flight",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="flightpermit",
            name="target_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="flightpermit",
            name="flight_duration",
            field=models.PositiveIntegerField(
                blank=True,
                help_text="Duration in hours",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="flightpermit",
            name="aircraft_configuration",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="flightpermit",
            name="conditions_restrictions",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="flightpermit",
            name="conditions_substantiations",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="flightpermit",
            name="is_recommendation",
            field=models.BooleanField(
                default=False,
                help_text="Indicates if the permit is a recommendation",
            ),
        ),
        migrations.RunPython(migrate_legacy_flight_permits, migrations.RunPython.noop),
        migrations.RemoveIndex(
            model_name="flightpermit",
            name="api_flightp_aircraf_f7a0fa_idx",
        ),
        migrations.RemoveField(model_name="flightpermit", name="aircraft_number"),
        migrations.RemoveField(model_name="flightpermit", name="permit_type"),
        migrations.RemoveField(model_name="flightpermit", name="issuing_authority"),
        migrations.RemoveField(model_name="flightpermit", name="flight_region"),
        migrations.AlterModelOptions(
            name="flightpermit",
            options={"ordering": ["valid_until", "serial_number", "permit_number"]},
        ),
        migrations.AddIndex(
            model_name="flightpermit",
            index=models.Index(
                fields=["serial_number", "valid_until"],
                name="api_flightp_serial__436c94_idx",
            ),
        ),
    ]
