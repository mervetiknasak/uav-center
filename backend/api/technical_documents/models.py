from django.conf import settings
from django.db import models


class CoverPage(models.Model):
    project = models.ForeignKey(
        "api.Project",
        related_name="cover_pages",
        on_delete=models.CASCADE,
    )
    number = models.CharField(max_length=80)
    issue = models.CharField(max_length=40)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["number", "issue"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "number", "issue"],
                name="unique_cover_page_number_issue_per_project",
            )
        ]

    def __str__(self):
        return f"{self.number} — Issue {self.issue}"


class TechnicalDocument(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_IN_REVIEW = "in_review"
    STATUS_CHANGES_REQUESTED = "changes_requested"
    STATUS_APPROVED = "approved"
    STATUS_PUBLISHED = "published"
    STATUS_SUPERSEDED = "superseded"
    STATUS_ARCHIVED = "archived"

    STATUS_CHOICES = [
        (STATUS_DRAFT, "Taslak"),
        (STATUS_IN_REVIEW, "İncelemede"),
        (STATUS_CHANGES_REQUESTED, "Revizyon Bekliyor"),
        (STATUS_APPROVED, "Onaylandı"),
        (STATUS_PUBLISHED, "Yayınlandı"),
        (STATUS_SUPERSEDED, "Yürürlükten Kalktı"),
        (STATUS_ARCHIVED, "Arşivlendi"),
    ]

    PRIORITY_NORMAL = "normal"
    PRIORITY_HIGH = "high"
    PRIORITY_CRITICAL = "critical"
    PRIORITY_CHOICES = [
        (PRIORITY_NORMAL, "Normal"),
        (PRIORITY_HIGH, "Yüksek"),
        (PRIORITY_CRITICAL, "Kritik"),
    ]

    CLASSIFICATION_INTERNAL = "internal"
    CLASSIFICATION_CONFIDENTIAL = "confidential"
    CLASSIFICATION_RESTRICTED = "restricted"
    CLASSIFICATION_PUBLIC = "public"
    CLASSIFICATION_CHOICES = [
        (CLASSIFICATION_INTERNAL, "Kurum İçi"),
        (CLASSIFICATION_CONFIDENTIAL, "Gizli"),
        (CLASSIFICATION_RESTRICTED, "Kısıtlı"),
        (CLASSIFICATION_PUBLIC, "Herkese Açık"),
    ]

    project = models.ForeignKey(
        "api.Project",
        related_name="technical_documents",
        on_delete=models.CASCADE,
    )
    cover_page = models.ForeignKey(
        CoverPage,
        related_name="technical_documents",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    panels = models.ManyToManyField(
        "api.ProjectPanel",
        related_name="technical_documents",
        blank=True,
    )
    code = models.CharField(max_length=80)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=120, blank=True)
    document_type = models.CharField(max_length=120, blank=True)
    revision = models.CharField(max_length=40, default="A")
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    priority = models.CharField(max_length=16, choices=PRIORITY_CHOICES, default=PRIORITY_NORMAL)
    classification = models.CharField(
        max_length=20,
        choices=CLASSIFICATION_CHOICES,
        default=CLASSIFICATION_INTERNAL,
    )
    owner_name = models.CharField(max_length=160, blank=True)
    publication_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    review_date = models.DateField(null=True, blank=True)
    source_url = models.URLField(blank=True)
    notes = models.TextField(blank=True)
    last_notification_at = models.DateTimeField(null=True, blank=True)
    last_notification_recipient_count = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="created_technical_documents",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="updated_technical_documents",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "code"],
                name="unique_technical_document_code_per_project",
            )
        ]
        indexes = [
            models.Index(fields=["project", "status"]),
            models.Index(fields=["due_date"]),
        ]

    def __str__(self):
        return f"{self.code} — {self.title}"


class TechnicalDocumentStatusHistory(models.Model):
    document = models.ForeignKey(
        TechnicalDocument,
        related_name="status_history",
        on_delete=models.CASCADE,
    )
    from_status = models.CharField(
        max_length=32,
        choices=TechnicalDocument.STATUS_CHOICES,
        blank=True,
    )
    to_status = models.CharField(max_length=32, choices=TechnicalDocument.STATUS_CHOICES)
    note = models.TextField(blank=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="technical_document_status_changes",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class TechnicalDocumentNotification(models.Model):
    STATUS_PENDING = "pending"
    STATUS_SENT = "sent"
    STATUS_FAILED = "failed"
    STATUS_UNKNOWN = "unknown"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Gönderiliyor"),
        (STATUS_SENT, "Gönderildi"),
        (STATUS_FAILED, "Başarısız"),
        (STATUS_UNKNOWN, "Sonuç belirsiz"),
    ]

    document = models.ForeignKey(
        TechnicalDocument,
        related_name="notifications",
        on_delete=models.CASCADE,
    )
    subject = models.CharField(max_length=255)
    message = models.TextField(blank=True)
    recipients = models.JSONField(default=list)
    recipient_count = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES)
    error_message = models.TextField(blank=True)
    idempotency_key = models.CharField(max_length=128, blank=True, default="")
    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="technical_document_notifications",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["document", "idempotency_key"],
                condition=~models.Q(idempotency_key=""),
                name="unique_notification_idempotency_key_per_document",
            )
        ]
