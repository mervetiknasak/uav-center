import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0011_asyncjob"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="FlightPermit",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("aircraft_number", models.CharField(max_length=80)),
                ("permit_number", models.CharField(max_length=100, unique=True)),
                (
                    "permit_type",
                    models.CharField(
                        choices=[
                            ("domestic", "Yurt İçi"),
                            ("international", "Uluslararası"),
                            ("test", "Test Uçuşu"),
                            ("ferry", "İntikal Uçuşu"),
                        ],
                        max_length=24,
                    ),
                ),
                ("issuing_authority", models.CharField(max_length=160)),
                ("flight_region", models.CharField(blank=True, max_length=200)),
                ("valid_from", models.DateField()),
                ("valid_until", models.DateField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Taslak"),
                            ("approved", "Onaylandı"),
                            ("suspended", "Askıya Alındı"),
                            ("revoked", "İptal Edildi"),
                        ],
                        default="draft",
                        max_length=16,
                    ),
                ),
                ("notes", models.TextField(blank=True)),
                ("document", models.FileField(blank=True, max_length=500, upload_to="flight_permits/%Y/%m/")),
                ("document_name", models.CharField(blank=True, max_length=255)),
                ("document_content_type", models.CharField(blank=True, max_length=120)),
                ("document_size", models.PositiveBigIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_flight_permits",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="updated_flight_permits",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["valid_until", "aircraft_number", "permit_number"]},
        ),
        migrations.AddIndex(
            model_name="flightpermit",
            index=models.Index(fields=["aircraft_number", "valid_until"], name="api_flightp_aircraf_f7a0fa_idx"),
        ),
        migrations.AddIndex(
            model_name="flightpermit",
            index=models.Index(fields=["status", "valid_until"], name="api_flightp_status_018897_idx"),
        ),
    ]
