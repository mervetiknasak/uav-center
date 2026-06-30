from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0003_project_projectpanel_panelresponsible"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="TechnicalDocument",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=80)),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                ("category", models.CharField(blank=True, max_length=120)),
                ("document_type", models.CharField(blank=True, max_length=120)),
                ("revision", models.CharField(default="A", max_length=40)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Taslak"),
                            ("in_review", "İncelemede"),
                            ("changes_requested", "Revizyon Bekliyor"),
                            ("approved", "Onaylandı"),
                            ("published", "Yayınlandı"),
                            ("superseded", "Yürürlükten Kalktı"),
                            ("archived", "Arşivlendi"),
                        ],
                        default="draft",
                        max_length=32,
                    ),
                ),
                (
                    "priority",
                    models.CharField(
                        choices=[("normal", "Normal"), ("high", "Yüksek"), ("critical", "Kritik")],
                        default="normal",
                        max_length=16,
                    ),
                ),
                (
                    "classification",
                    models.CharField(
                        choices=[
                            ("internal", "Kurum İçi"),
                            ("confidential", "Gizli"),
                            ("restricted", "Kısıtlı"),
                            ("public", "Herkese Açık"),
                        ],
                        default="internal",
                        max_length=20,
                    ),
                ),
                ("owner_name", models.CharField(blank=True, max_length=160)),
                ("publication_date", models.DateField(blank=True, null=True)),
                ("due_date", models.DateField(blank=True, null=True)),
                ("review_date", models.DateField(blank=True, null=True)),
                ("source_url", models.URLField(blank=True)),
                ("notes", models.TextField(blank=True)),
                ("last_notification_at", models.DateTimeField(blank=True, null=True)),
                ("last_notification_recipient_count", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_technical_documents",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="technical_documents",
                        to="api.project",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="updated_technical_documents",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "panels",
                    models.ManyToManyField(blank=True, related_name="technical_documents", to="api.projectpanel"),
                ),
            ],
            options={"ordering": ["-updated_at", "code"]},
        ),
        migrations.CreateModel(
            name="TechnicalDocumentStatusHistory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "from_status",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("draft", "Taslak"),
                            ("in_review", "İncelemede"),
                            ("changes_requested", "Revizyon Bekliyor"),
                            ("approved", "Onaylandı"),
                            ("published", "Yayınlandı"),
                            ("superseded", "Yürürlükten Kalktı"),
                            ("archived", "Arşivlendi"),
                        ],
                        max_length=32,
                    ),
                ),
                (
                    "to_status",
                    models.CharField(
                        choices=[
                            ("draft", "Taslak"),
                            ("in_review", "İncelemede"),
                            ("changes_requested", "Revizyon Bekliyor"),
                            ("approved", "Onaylandı"),
                            ("published", "Yayınlandı"),
                            ("superseded", "Yürürlükten Kalktı"),
                            ("archived", "Arşivlendi"),
                        ],
                        max_length=32,
                    ),
                ),
                ("note", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "changed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="technical_document_status_changes",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "document",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="status_history",
                        to="api.technicaldocument",
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="TechnicalDocumentNotification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("subject", models.CharField(max_length=255)),
                ("message", models.TextField(blank=True)),
                ("recipients", models.JSONField(default=list)),
                ("recipient_count", models.PositiveIntegerField(default=0)),
                ("status", models.CharField(choices=[("sent", "Gönderildi"), ("failed", "Başarısız")], max_length=16)),
                ("error_message", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "document",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notifications",
                        to="api.technicaldocument",
                    ),
                ),
                (
                    "sent_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="technical_document_notifications",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddConstraint(
            model_name="technicaldocument",
            constraint=models.UniqueConstraint(
                fields=("project", "code"),
                name="unique_technical_document_code_per_project",
            ),
        ),
        migrations.AddIndex(
            model_name="technicaldocument",
            index=models.Index(fields=["project", "status"], name="api_technic_project_e11035_idx"),
        ),
        migrations.AddIndex(
            model_name="technicaldocument",
            index=models.Index(fields=["due_date"], name="api_technic_due_dat_7a4756_idx"),
        ),
    ]
