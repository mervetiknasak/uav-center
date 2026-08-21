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
    meeting_title = models.CharField(max_length=240)
    project_name = models.CharField(max_length=160)
    requested_date = models.DateField()
    location = models.CharField(max_length=200)
    participants = models.TextField(max_length=2000)
    purpose = models.TextField(max_length=3000)
    agenda = models.TextField(max_length=5000)
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
        return f"EDK-{self.pk or 'yeni'} — {self.meeting_title}"
