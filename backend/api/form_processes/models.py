import uuid

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
    attachment = models.FileField(
        upload_to="form_processes/%Y/%m/",
        max_length=500,
        blank=True,
    )
    attachment_name = models.CharField(max_length=255, blank=True)
    attachment_content_type = models.CharField(max_length=120, blank=True)
    attachment_size = models.PositiveBigIntegerField(default=0)
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


class FormNumberMapping(models.Model):
    template_code = models.CharField(max_length=64)
    target_field = models.CharField(max_length=128)
    format_code = models.SlugField(max_length=50)
    enabled = models.BooleanField(default=True)
    context_sources = models.JSONField(default=dict)
    format_snapshot = models.JSONField(default=dict)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["template_code", "target_field"]
        constraints = [
            models.UniqueConstraint(
                fields=["template_code", "target_field"], name="unique_form_number_target"
            )
        ]


class FormNumberAllocation(models.Model):
    """An immutable provider request; survives record deletion and interrupted HTTP calls."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    idempotency_key = models.CharField(max_length=128, unique=True)
    request_hash = models.CharField(max_length=64)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    record = models.ForeignKey(
        FormProcessRecord, on_delete=models.SET_NULL, null=True, related_name="number_allocations"
    )
    original_record_id = models.PositiveBigIntegerField(null=True)
    mapping = models.ForeignKey(FormNumberMapping, on_delete=models.PROTECT)
    target_field = models.CharField(max_length=128)
    mapping_snapshot = models.JSONField(default=dict)
    form_snapshot = models.JSONField(default=dict)
    provider_payload = models.JSONField(default=dict)
    locked_values = models.JSONField(default=dict)
    expected_updated_at = models.DateTimeField(null=True)
    attachment = models.FileField(upload_to="form_numbering/%Y/%m/", max_length=500, blank=True)
    attachment_name = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=16, default="pending")
    provider_id = models.PositiveBigIntegerField(null=True)
    document_number = models.TextField(blank=True)
    lease_token = models.UUIDField(null=True)
    lease_until = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["record", "target_field"], name="unique_form_number_allocation_target"
            )
        ]


class FormNumberingConfigLock(models.Model):
    """Serialize changes to a template's dependency graph, including first inserts."""

    template_code = models.CharField(max_length=64, primary_key=True)
