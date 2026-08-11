from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0014_alter_document_owner_on_delete"),
    ]

    operations = [
        migrations.AddField(
            model_name="technicaldocumentnotification",
            name="idempotency_key",
            field=models.CharField(blank=True, default="", max_length=128),
        ),
        migrations.AlterField(
            model_name="technicaldocumentnotification",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Gönderiliyor"),
                    ("sent", "Gönderildi"),
                    ("failed", "Başarısız"),
                ],
                max_length=16,
            ),
        ),
        migrations.AddConstraint(
            model_name="technicaldocumentnotification",
            constraint=models.UniqueConstraint(
                condition=~models.Q(idempotency_key=""),
                fields=("document", "idempotency_key"),
                name="unique_notification_idempotency_key_per_document",
            ),
        ),
    ]
