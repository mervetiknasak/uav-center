from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0015_notification_idempotency"),
    ]

    operations = [
        migrations.AlterField(
            model_name="technicaldocumentnotification",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Gönderiliyor"),
                    ("sent", "Gönderildi"),
                    ("failed", "Başarısız"),
                    ("unknown", "Sonuç belirsiz"),
                ],
                max_length=16,
            ),
        ),
    ]
