from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0008_person_person_group"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="panelresponsible",
            name="phone",
        ),
        migrations.RemoveField(
            model_name="person",
            name="phone",
        ),
    ]
