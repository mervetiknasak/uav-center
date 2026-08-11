from django.conf import settings
from django.db import models
from django.utils import timezone


class FlightPermit(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_APPROVED = "approved"
    STATUS_SUSPENDED = "suspended"
    STATUS_REVOKED = "revoked"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Taslak"),
        (STATUS_APPROVED, "Onaylandı"),
        (STATUS_SUSPENDED, "Askıya Alındı"),
        (STATUS_REVOKED, "İptal Edildi"),
    ]

    TYPE_DOMESTIC = "domestic"
    TYPE_INTERNATIONAL = "international"
    TYPE_TEST = "test"
    TYPE_FERRY = "ferry"
    TYPE_CHOICES = [
        (TYPE_DOMESTIC, "Yurt İçi"),
        (TYPE_INTERNATIONAL, "Uluslararası"),
        (TYPE_TEST, "Test Uçuşu"),
        (TYPE_FERRY, "İntikal Uçuşu"),
    ]

    aircraft_number = models.CharField(max_length=80)
    permit_number = models.CharField(max_length=100, unique=True)
    permit_type = models.CharField(max_length=24, choices=TYPE_CHOICES)
    issuing_authority = models.CharField(max_length=160)
    flight_region = models.CharField(max_length=200, blank=True)
    valid_from = models.DateField()
    valid_until = models.DateField()
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    notes = models.TextField(blank=True)
    document = models.FileField(
        upload_to="flight_permits/%Y/%m/",
        max_length=500,
        blank=True,
    )
    document_name = models.CharField(max_length=255, blank=True)
    document_content_type = models.CharField(max_length=120, blank=True)
    document_size = models.PositiveBigIntegerField(default=0)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="created_flight_permits",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="updated_flight_permits",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["valid_until", "aircraft_number", "permit_number"]
        indexes = [
            models.Index(fields=["aircraft_number", "valid_until"]),
            models.Index(fields=["status", "valid_until"]),
        ]

    def __str__(self):
        return f"{self.aircraft_number} — {self.permit_number}"

    def validity_status(self, *, on_date=None):
        """Return the effective validity state for a calendar date."""

        reference_date = on_date or timezone.localdate()
        if self.status in {self.STATUS_SUSPENDED, self.STATUS_REVOKED}:
            return self.status
        if self.status == self.STATUS_DRAFT:
            return "draft"
        if self.valid_from > reference_date:
            return "upcoming"
        if self.valid_until < reference_date:
            return "expired"
        if (self.valid_until - reference_date).days <= 30:
            return "expiring"
        return "active"
