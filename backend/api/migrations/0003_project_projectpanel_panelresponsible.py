from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("api", "0002_document_prompt")]

    operations = [
        migrations.CreateModel(
            name="Project",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=160)),
                ("code", models.CharField(max_length=40, unique=True)),
                ("description", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
                ("order", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["order", "name"]},
        ),
        migrations.CreateModel(
            name="ProjectPanel",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=160)),
                ("description", models.TextField(blank=True)),
                ("order", models.PositiveIntegerField(default=0)),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="panels", to="api.project")),
            ],
            options={"ordering": ["order", "name"]},
        ),
        migrations.CreateModel(
            name="PanelResponsible",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=160)),
                ("title", models.CharField(blank=True, max_length=160)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("phone", models.CharField(blank=True, max_length=40)),
                ("order", models.PositiveIntegerField(default=0)),
                ("panel", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="responsibles", to="api.projectpanel")),
            ],
            options={"ordering": ["order", "name"]},
        ),
        migrations.AddConstraint(
            model_name="projectpanel",
            constraint=models.UniqueConstraint(fields=("project", "name"), name="unique_panel_name_per_project"),
        ),
    ]
