from django.db import models
from django.conf import settings


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

    def __str__(self):
        return self.original_name


class Project(models.Model):
    name = models.CharField(max_length=160)
    code = models.CharField(max_length=40, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class ProjectPanel(models.Model):
    project = models.ForeignKey(Project, related_name="panels", on_delete=models.CASCADE)
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]
        constraints = [
            models.UniqueConstraint(fields=["project", "name"], name="unique_panel_name_per_project")
        ]

    def __str__(self):
        return f"{self.project.code} / {self.name}"


class PanelResponsible(models.Model):
    panel = models.ForeignKey(ProjectPanel, related_name="responsibles", on_delete=models.CASCADE)
    name = models.CharField(max_length=160)
    title = models.CharField(max_length=160, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    username = models.CharField(max_length=160, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class CoverPage(models.Model):
    project = models.ForeignKey(Project, related_name="cover_pages", on_delete=models.CASCADE)
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

    project = models.ForeignKey(Project, related_name="technical_documents", on_delete=models.CASCADE)
    cover_page = models.ForeignKey(
        CoverPage,
        related_name="technical_documents",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    panels = models.ManyToManyField(ProjectPanel, related_name="technical_documents", blank=True)
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
    STATUS_SENT = "sent"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_SENT, "Gönderildi"),
        (STATUS_FAILED, "Başarısız"),
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
