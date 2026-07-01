from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0006_rename_jira_username_panelresponsible_username"),
    ]

    operations = [
        migrations.CreateModel(
            name="CoverPage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("number", models.CharField(max_length=80)),
                ("issue", models.CharField(max_length=40)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="cover_pages",
                        to="api.project",
                    ),
                ),
            ],
            options={
                "ordering": ["number", "issue"],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("project", "number", "issue"),
                        name="unique_cover_page_number_issue_per_project",
                    )
                ],
            },
        ),
        migrations.AddField(
            model_name="technicaldocument",
            name="cover_page",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="technical_documents",
                to="api.coverpage",
            ),
        ),
    ]
