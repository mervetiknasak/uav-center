from django.conf import settings
from django.db import models


class EDKApplication(models.Model):
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Onay Bekliyor"),
        (STATUS_APPROVED, "Onaylandı"),
        (STATUS_REJECTED, "Reddedildi"),
    ]

    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="edk_applications",
        on_delete=models.PROTECT,
    )
    aircraft_name = models.CharField(max_length=160)
    tail_number = models.CharField(max_length=80, blank=True)
    scope = models.TextField(max_length=5000, blank=True)
    project = models.ForeignKey(
        "api.Project",
        related_name="edk_applications",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    presentation = models.FileField(
        upload_to="edk/presentations/%Y/%m/",
        max_length=500,
        blank=True,
    )
    presentation_file_name = models.CharField(max_length=255, blank=True)
    presentation_content_type = models.CharField(max_length=120, blank=True)
    presentation_size = models.PositiveBigIntegerField(default=0)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    decision_note = models.TextField(max_length=2000, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="reviewed_edk_applications",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    minutes_file_name = models.CharField(max_length=255, blank=True)
    minutes_uploaded_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(
                fields=["applicant", "status", "created_at"],
                name="api_edk_applicant_status_idx",
            ),
            models.Index(
                fields=["status", "created_at"],
                name="api_edk_status_created_idx",
            ),
        ]

    def __str__(self):
        return f"EDK-{self.pk or 'yeni'} — {self.aircraft_name}"
