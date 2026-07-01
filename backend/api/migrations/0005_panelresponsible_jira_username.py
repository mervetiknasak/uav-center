from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0004_technical_documents"),
    ]

    operations = [
        migrations.AddField(
            model_name="panelresponsible",
            name="jira_username",
            field=models.CharField(blank=True, max_length=160),
        ),
    ]
