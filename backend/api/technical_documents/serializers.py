from rest_framework import serializers

from ..common.serializer_fields import UserDisplayNameField
from ..organization.models import ProjectPanel
from .models import (
    CoverPage,
    TechnicalDocument,
    TechnicalDocumentNotification,
    TechnicalDocumentStatusHistory,
)
from .services.lifecycle import create_technical_document, update_technical_document


class TechnicalDocumentPanelSerializer(serializers.ModelSerializer):
    responsible_count = serializers.IntegerField(source="responsibles.count", read_only=True)

    class Meta:
        model = ProjectPanel
        fields = ["id", "name", "responsible_count"]


class TechnicalDocumentStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_name = UserDisplayNameField(source="changed_by")
    from_status_display = serializers.CharField(source="get_from_status_display", read_only=True)
    to_status_display = serializers.CharField(source="get_to_status_display", read_only=True)

    class Meta:
        model = TechnicalDocumentStatusHistory
        fields = [
            "id",
            "from_status",
            "from_status_display",
            "to_status",
            "to_status_display",
            "note",
            "changed_by_name",
            "created_at",
        ]


class TechnicalDocumentNotificationSerializer(serializers.ModelSerializer):
    sent_by_name = UserDisplayNameField(source="sent_by")

    class Meta:
        model = TechnicalDocumentNotification
        fields = [
            "id",
            "subject",
            "message",
            "recipients",
            "recipient_count",
            "status",
            "error_message",
            "idempotency_key",
            "sent_by_name",
            "created_at",
        ]


class TechnicalDocumentNotificationSummarySerializer(serializers.ModelSerializer):
    """Non-sensitive notification audit projection for non-staff readers."""

    sent_by_name = UserDisplayNameField(source="sent_by")

    class Meta:
        model = TechnicalDocumentNotification
        fields = [
            "id",
            "recipient_count",
            "status",
            "sent_by_name",
            "created_at",
        ]


class CoverPageSerializer(serializers.ModelSerializer):
    number = serializers.CharField(max_length=80, trim_whitespace=True)
    issue = serializers.CharField(max_length=40, trim_whitespace=True)

    class Meta:
        model = CoverPage
        fields = ["id", "number", "issue"]
        read_only_fields = ["id"]


class TechnicalDocumentSerializer(serializers.ModelSerializer):
    panels = serializers.PrimaryKeyRelatedField(
        queryset=ProjectPanel.objects.select_related("project"),
        many=True,
        required=False,
        write_only=True,
    )
    panel_details = TechnicalDocumentPanelSerializer(source="panels", many=True, read_only=True)
    project_name = serializers.CharField(source="project.name", read_only=True)
    project_code = serializers.CharField(source="project.code", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    priority_display = serializers.CharField(source="get_priority_display", read_only=True)
    classification_display = serializers.CharField(
        source="get_classification_display", read_only=True
    )
    notification_recipients = serializers.SerializerMethodField()
    status_history = TechnicalDocumentStatusHistorySerializer(many=True, read_only=True)
    notifications = serializers.SerializerMethodField()
    created_by_name = UserDisplayNameField(source="created_by")
    updated_by_name = UserDisplayNameField(source="updated_by")
    cover_page = CoverPageSerializer(required=False, allow_null=True)
    status_note = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=2000,
        write_only=True,
    )

    class Meta:
        model = TechnicalDocument
        fields = [
            "id",
            "project",
            "project_name",
            "project_code",
            "cover_page",
            "panels",
            "panel_details",
            "code",
            "title",
            "description",
            "category",
            "document_type",
            "revision",
            "status",
            "status_note",
            "status_display",
            "priority",
            "priority_display",
            "classification",
            "classification_display",
            "owner_name",
            "publication_date",
            "due_date",
            "review_date",
            "source_url",
            "notes",
            "notification_recipients",
            "last_notification_at",
            "last_notification_recipient_count",
            "status_history",
            "notifications",
            "created_by_name",
            "updated_by_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "last_notification_at",
            "last_notification_recipient_count",
            "created_at",
            "updated_at",
        ]

    def get_notification_recipients(self, document):
        request = self.context.get("request")
        if not getattr(getattr(request, "user", None), "is_staff", False):
            return []
        recipients = {}
        for panel in document.panels.all():
            for responsible in panel.responsibles.all():
                if responsible.email:
                    recipients[responsible.email.lower()] = {
                        "name": responsible.name,
                        "email": responsible.email,
                        "panel": panel.name,
                    }
        return list(recipients.values())

    def get_notifications(self, document):
        request = self.context.get("request")
        serializer_class = (
            TechnicalDocumentNotificationSerializer
            if getattr(getattr(request, "user", None), "is_staff", False)
            else TechnicalDocumentNotificationSummarySerializer
        )
        return serializer_class(document.notifications.all(), many=True).data

    def validate_code(self, value):
        return value.strip().upper()

    def validate(self, attrs):
        project = attrs.get("project", getattr(self.instance, "project", None))
        panels = attrs.get("panels")
        status_value = attrs.get(
            "status", getattr(self.instance, "status", TechnicalDocument.STATUS_DRAFT)
        )
        publication_date = attrs.get(
            "publication_date",
            getattr(self.instance, "publication_date", None),
        )
        cover_page = attrs.get("cover_page", serializers.empty)
        project_changed = bool(self.instance and project and project.id != self.instance.project_id)

        if panels is not None and project:
            invalid_panels = [panel.name for panel in panels if panel.project_id != project.id]
            if invalid_panels:
                raise serializers.ValidationError(
                    {
                        "panels": [
                            f"Seçilen paneller bu projeye ait değil: {', '.join(invalid_panels)}"
                        ]
                    }
                )
        elif (
            self.instance
            and project
            and project.id != self.instance.project_id
            and self.instance.panels.exclude(project_id=project.id).exists()
        ):
            raise serializers.ValidationError(
                {
                    "panels": [
                        "Proje değiştirilirken yeni projeye ait panel seçimi de gönderilmelidir."
                    ]
                }
            )

        if status_value == TechnicalDocument.STATUS_PUBLISHED and not publication_date:
            raise serializers.ValidationError(
                {"publication_date": ["Yayınlanan bir doküman için yayın tarihi zorunludur."]}
            )

        if (
            self.instance
            and status_value != self.instance.status
            and not attrs.get("status_note", "").strip()
        ):
            raise serializers.ValidationError(
                {"status_note": ["Durum değişikliğinde açıklama zorunludur."]}
            )

        if project_changed and self.instance.cover_page_id and cover_page is serializers.empty:
            raise serializers.ValidationError(
                {
                    "cover_page": [
                        "Proje değiştirilirken yeni projeye ait kapak sayfası "
                        "gönderilmeli veya alan null yapılmalıdır."
                    ]
                }
            )

        if cover_page is not serializers.empty and cover_page is not None:
            if not cover_page.get("number") or not cover_page.get("issue"):
                raise serializers.ValidationError(
                    {"cover_page": ["Kapak sayfası numarası ve issue birlikte girilmelidir."]}
                )

        return attrs

    def create(self, validated_data):
        return create_technical_document(
            validated_data=validated_data,
            actor=self.context["request"].user,
        )

    def update(self, instance, validated_data):
        return update_technical_document(
            document=instance,
            validated_data=validated_data,
            actor=self.context["request"].user,
        )


class TechnicalDocumentNotificationRequestSerializer(serializers.Serializer):
    subject = serializers.CharField(max_length=255, required=False, allow_blank=True)
    message = serializers.CharField(max_length=5000, required=False, allow_blank=True)


class NotificationIdempotencyKeySerializer(serializers.Serializer):
    idempotency_key = serializers.RegexField(
        regex=r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$",
        error_messages={
            "required": "Idempotency-Key başlığı zorunludur.",
            "invalid": (
                "Idempotency-Key 8-128 karakter olmalı ve yalnız harf, rakam, nokta, "
                "alt çizgi, iki nokta veya tire içermelidir."
            ),
        },
    )
