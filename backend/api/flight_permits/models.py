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

    permit_applicant = models.TextField()
    permit_number = models.CharField(max_length=100, unique=True)
    aircraft_nationality = models.CharField(max_length=64, blank=True)
    aircraft_id_mark = models.CharField(max_length=64, blank=True)
    aircraft_owner = models.CharField(max_length=64, blank=True)
    aircraft_type = models.CharField(max_length=64, blank=True)
    aircraft_manufacturer = models.CharField(max_length=64, blank=True)
    serial_number = models.CharField(max_length=64, blank=True)
    purpose_of_flight = models.JSONField(default=list, blank=True)
    target_date = models.DateField(null=True, blank=True)
    flight_duration = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Duration in hours",
    )
    aircraft_configuration = models.TextField(blank=True)
    conditions_restrictions = models.TextField(blank=True)
    conditions_substantiations = models.TextField(blank=True)
    is_recommendation = models.BooleanField(
        default=False,
        help_text="Indicates if the permit is a recommendation",
    )
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
        ordering = ["valid_until", "serial_number", "permit_number"]
        indexes = [
            models.Index(fields=["serial_number", "valid_until"]),
            models.Index(fields=["status", "valid_until"]),
        ]

    def __str__(self):
        return f"{self.permit_number} — {self.serial_number}"

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
