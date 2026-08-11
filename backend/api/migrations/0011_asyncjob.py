import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0010_analysiscontrol_documentanalysisrun_documentchunk"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AsyncJob",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("job_type", models.CharField(choices=[("document_processing", "Belge işleme")], max_length=48)),
                ("status", models.CharField(choices=[("queued", "Sırada"), ("running", "Çalışıyor"), ("completed", "Tamamlandı"), ("failed", "Başarısız"), ("cancelled", "İptal edildi")], default="queued", max_length=16)),
                ("priority", models.SmallIntegerField(default=0)),
                ("progress", models.PositiveSmallIntegerField(default=0)),
                ("payload", models.JSONField(blank=True, default=dict)),
                ("result", models.JSONField(blank=True, default=dict)),
                ("error_message", models.TextField(blank=True)),
                ("attempts", models.PositiveSmallIntegerField(default=0)),
                ("max_attempts", models.PositiveSmallIntegerField(default=3)),
                ("available_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("locked_at", models.DateTimeField(blank=True, null=True)),
                ("locked_by", models.CharField(blank=True, max_length=160)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("document", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="jobs", to="api.document")),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="async_jobs", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["status", "available_at", "-priority", "created_at"], name="api_asyncjo_status_4ee149_idx"),
                    models.Index(fields=["owner", "-created_at"], name="api_asyncjo_owner_i_205a5b_idx"),
                    models.Index(fields=["owner", "status", "-created_at"], name="api_asyncjo_owner_i_584d84_idx"),
                ],
            },
        ),
    ]
