from django.conf import settings
from django.db import models


class FormProcessRecord(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_IN_REVIEW = "in_review"
    STATUS_APPROVED = "approved"
    STATUS_ARCHIVED = "archived"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Taslak"),
        (STATUS_IN_REVIEW, "İncelemede"),
        (STATUS_APPROVED, "Onaylandı"),
        (STATUS_ARCHIVED, "Arşivlendi"),
    ]

    process_code = models.CharField(max_length=64, db_index=True)
    template_code = models.CharField(max_length=64, db_index=True)
    record_number = models.CharField(max_length=128)
    title = models.CharField(max_length=300)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    data = models.JSONField(default=dict)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="created_form_process_records",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="updated_form_process_records",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at", "record_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["process_code", "record_number"],
                name="unique_form_record_number_per_process",
            )
        ]
        indexes = [
            models.Index(
                fields=["process_code", "status", "updated_at"],
                name="api_formpro_process_b3f6c6_idx",
            )
        ]

    def __str__(self):
        return f"{self.record_number} — {self.title}"
