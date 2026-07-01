from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0005_panelresponsible_jira_username"),
    ]

    operations = [
        migrations.RenameField(
            model_name="panelresponsible",
            old_name="jira_username",
            new_name="username",
        ),
    ]
