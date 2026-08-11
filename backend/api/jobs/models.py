import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class AsyncJob(models.Model):
    """A durable unit of background work owned by one application user."""

    TYPE_DOCUMENT_PROCESSING = "document_processing"
    TYPE_CHOICES = [
        (TYPE_DOCUMENT_PROCESSING, "Belge işleme"),
    ]

    STATUS_QUEUED = "queued"
    STATUS_RUNNING = "running"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_QUEUED, "Sırada"),
        (STATUS_RUNNING, "Çalışıyor"),
        (STATUS_COMPLETED, "Tamamlandı"),
        (STATUS_FAILED, "Başarısız"),
        (STATUS_CANCELLED, "İptal edildi"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="async_jobs",
        on_delete=models.CASCADE,
    )
    job_type = models.CharField(max_length=48, choices=TYPE_CHOICES)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_QUEUED)
    priority = models.SmallIntegerField(default=0)
    progress = models.PositiveSmallIntegerField(default=0)
    payload = models.JSONField(default=dict, blank=True)
    result = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    max_attempts = models.PositiveSmallIntegerField(default=3)
    available_at = models.DateTimeField(default=timezone.now)
    locked_at = models.DateTimeField(null=True, blank=True)
    locked_by = models.CharField(max_length=160, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    document = models.ForeignKey(
        "api.Document",
        related_name="jobs",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "available_at", "-priority", "created_at"]),
            models.Index(fields=["owner", "-created_at"]),
            models.Index(fields=["owner", "status", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.job_type}:{self.id}"
