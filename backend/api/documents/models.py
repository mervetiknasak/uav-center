from django.conf import settings
from django.db import models


class Document(models.Model):
    STATUS_PENDING = "pending"
    STATUS_PROCESSED = "processed"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PROCESSED, "Processed"),
        (STATUS_FAILED, "Failed"),
    ]

    original_name = models.CharField(max_length=255)
    file = models.FileField(upload_to="documents/%Y/%m/%d/")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="documents",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    content_type = models.CharField(max_length=120, blank=True)
    size = models.PositiveBigIntegerField(default=0)
    prompt = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    extracted_text = models.TextField(blank=True)
    ai_result = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["owner", "-created_at"],
                name="api_doc_owner_created_idx",
            )
        ]

    def __str__(self):
        return self.original_name


class DocumentChunk(models.Model):
    """A stable, citable slice of extracted document text used by RAG."""

    document = models.ForeignKey(Document, related_name="chunks", on_delete=models.CASCADE)
    position = models.PositiveIntegerField()
    content = models.TextField()
    char_start = models.PositiveIntegerField()
    char_end = models.PositiveIntegerField()
    word_count = models.PositiveIntegerField(default=0)
    content_hash = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["document_id", "position"]
        constraints = [
            models.UniqueConstraint(
                fields=["document", "position"],
                name="unique_chunk_position_per_document",
            )
        ]
        indexes = [models.Index(fields=["document", "position"])]

    def __str__(self):
        return f"{self.document_id}:{self.position}"


class AnalysisControl(models.Model):
    """A reusable document check created from the UI by an authenticated user."""

    SEVERITY_INFO = "info"
    SEVERITY_WARNING = "warning"
    SEVERITY_CRITICAL = "critical"
    SEVERITY_CHOICES = [
        (SEVERITY_INFO, "Bilgi"),
        (SEVERITY_WARNING, "Uyarı"),
        (SEVERITY_CRITICAL, "Kritik"),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="analysis_controls",
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    instructions = models.TextField()
    severity = models.CharField(
        max_length=16,
        choices=SEVERITY_CHOICES,
        default=SEVERITY_WARNING,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "name"],
                name="unique_analysis_control_name_per_owner",
            )
        ]

    def __str__(self):
        return self.name


class DocumentAnalysisRun(models.Model):
    STATUS_PENDING = "pending"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_PENDING, "İşleniyor"),
        (STATUS_COMPLETED, "Tamamlandı"),
        (STATUS_FAILED, "Başarısız"),
    ]

    document = models.ForeignKey(Document, related_name="analysis_runs", on_delete=models.CASCADE)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="document_analysis_runs",
        on_delete=models.SET_NULL,
        null=True,
    )
    query = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES)
    controls = models.JSONField(default=list, blank=True)
    result = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["document", "-created_at"])]
