from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0025_update_edk_application_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="edkapplication",
            name="jira_issue_key",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="edkapplication",
            name="jira_last_synced_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="edkapplication",
            name="jira_status",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name="edkapplication",
            name="jira_subtasks",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="edkapplication",
            name="jira_summary",
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name="edkapplication",
            name="jira_url",
            field=models.URLField(blank=True, max_length=500),
        ),
        migrations.AddConstraint(
            model_name="edkapplication",
            constraint=models.UniqueConstraint(
                condition=~Q(jira_issue_key=""),
                fields=("jira_issue_key",),
                name="api_edk_unique_jira_issue_key",
            ),
        ),
    ]
