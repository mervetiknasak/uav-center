import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0024_edkapplication"),
    ]

    operations = [
        migrations.AddField(
            model_name="edkapplication",
            name="aircraft_name",
            field=models.CharField(default="", max_length=160),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="edkapplication",
            name="presentation",
            field=models.FileField(
                blank=True,
                max_length=500,
                upload_to="edk/presentations/%Y/%m/",
            ),
        ),
        migrations.AddField(
            model_name="edkapplication",
            name="presentation_content_type",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name="edkapplication",
            name="presentation_file_name",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="edkapplication",
            name="presentation_size",
            field=models.PositiveBigIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="edkapplication",
            name="project",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="edk_applications",
                to="api.project",
            ),
        ),
        migrations.AddField(
            model_name="edkapplication",
            name="scheduled_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="edkapplication",
            name="scope",
            field=models.TextField(blank=True, max_length=5000),
        ),
        migrations.AddField(
            model_name="edkapplication",
            name="tail_number",
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.RemoveField(model_name="edkapplication", name="agenda"),
        migrations.RemoveField(model_name="edkapplication", name="location"),
        migrations.RemoveField(model_name="edkapplication", name="meeting_title"),
        migrations.RemoveField(model_name="edkapplication", name="participants"),
        migrations.RemoveField(model_name="edkapplication", name="project_name"),
        migrations.RemoveField(model_name="edkapplication", name="purpose"),
        migrations.RemoveField(model_name="edkapplication", name="requested_date"),
    ]
