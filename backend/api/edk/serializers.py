"""Request DTOs for meeting-minutes HTTP use cases."""

from collections.abc import Mapping
from datetime import timedelta
from pathlib import Path

from django.utils import timezone
from rest_framework import serializers

from ..common.serializer_fields import UserDisplayNameField
from ..organization.models import Project
from ..services.document_limits import (
    DocumentPreflightError,
    preflight_document,
    validate_upload_size,
)
from .file_policy import EDK_PRESENTATION_EXTENSIONS
from .models import EDKApplication
from .services import create_edk_application, jira_tracking_payload


class EDKApplicationSerializer(serializers.ModelSerializer):
    applicant_name = serializers.CharField(source="applicant.username", read_only=True)
    project = serializers.PrimaryKeyRelatedField(
        queryset=Project.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )
    project_display = serializers.SerializerMethodField()
    reviewed_by_name = UserDisplayNameField(source="reviewed_by")
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    can_upload_minutes = serializers.SerializerMethodField()
    presentation_url = serializers.SerializerMethodField()
    jira_tracking = serializers.SerializerMethodField()

    class Meta:
        model = EDKApplication
        fields = [
            "id",
            "applicant_name",
            "aircraft_name",
            "tail_number",
            "scope",
            "project",
            "project_display",
            "presentation",
            "presentation_file_name",
            "presentation_content_type",
            "presentation_size",
            "presentation_url",
            "scheduled_at",
            "status",
            "status_display",
            "decision_note",
            "reviewed_by_name",
            "reviewed_at",
            "minutes_file_name",
            "minutes_uploaded_at",
            "jira_tracking",
            "can_upload_minutes",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {
            "presentation": {"write_only": True, "required": False},
        }
        read_only_fields = [
            "status",
            "decision_note",
            "reviewed_by_name",
            "reviewed_at",
            "presentation_file_name",
            "presentation_content_type",
            "presentation_size",
            "presentation_url",
            "minutes_file_name",
            "minutes_uploaded_at",
            "jira_tracking",
            "created_at",
            "updated_at",
        ]

    def get_can_upload_minutes(self, application):
        request = self.context.get("request")
        return bool(
            request
            and request.user.id == application.applicant_id
            and application.status == EDKApplication.STATUS_APPROVED
        )

    def get_presentation_url(self, application):
        if not application.presentation:
            return ""
        return f"/api/edk/applications/{application.pk}/presentation/"

    def get_project_display(self, application):
        if not application.project:
            return ""
        return f"{application.project.code} — {application.project.name}"

    def get_jira_tracking(self, application):
        return jira_tracking_payload(application)

    def validate_aircraft_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Bu alan zorunludur.")
        return value

    def validate_tail_number(self, value):
        return value.strip()

    def validate_scope(self, value):
        return value.strip()

    def validate_presentation(self, uploaded_file):
        suffix = Path(uploaded_file.name).suffix.lower()
        if suffix not in EDK_PRESENTATION_EXTENSIONS:
            allowed = ", ".join(sorted(EDK_PRESENTATION_EXTENSIONS))
            raise serializers.ValidationError(
                f"Desteklenmeyen dosya tipi. Desteklenenler: {allowed}"
            )
        try:
            validate_upload_size(uploaded_file.size)
            preflight_document(uploaded_file, suffix)
        except DocumentPreflightError as exc:
            raise serializers.ValidationError(str(exc)) from exc
        return uploaded_file

    def validate_scheduled_at(self, value):
        local_date = timezone.localtime(value).date()
        minimum_date = timezone.localdate() + timedelta(days=7)
        if local_date < minimum_date:
            raise serializers.ValidationError("Tarih bugünden en az 7 gün sonrası olmalıdır.")
        return value

    def create(self, validated_data):
        return create_edk_application(
            validated_data=validated_data,
            applicant=self.context["request"].user,
        )


class EDKApplicationDecisionSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=[EDKApplication.STATUS_APPROVED, EDKApplication.STATUS_REJECTED]
    )
    decision_note = serializers.CharField(required=False, allow_blank=True, max_length=2000)

    def validate(self, attrs):
        note = attrs.get("decision_note", "").strip()
        if attrs["status"] == EDKApplication.STATUS_REJECTED and not note:
            raise serializers.ValidationError({"decision_note": ["Reddetme gerekçesi zorunludur."]})
        attrs["decision_note"] = note
        return attrs


class JiraMeetingFieldSerializer(serializers.Serializer):
    key = serializers.CharField(required=False, allow_blank=True)
    label = serializers.CharField(required=False, allow_blank=True)
    value = serializers.CharField(required=False, allow_blank=True)
    enabled = serializers.BooleanField(required=False)


class JiraTaskSerializer(serializers.Serializer):
    project_key = serializers.CharField(trim_whitespace=True)
    summary = serializers.CharField(trim_whitespace=True)
    issue_type = serializers.CharField(required=False, allow_blank=True)
    meeting_fields = JiraMeetingFieldSerializer(many=True, required=False)
    labels = serializers.ListField(
        child=serializers.CharField(allow_blank=True),
        required=False,
    )


class JiraSubtaskSerializer(serializers.Serializer):
    client_id = serializers.CharField(required=False, allow_blank=True)
    enabled = serializers.BooleanField(required=False)
    summary = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)
    description = serializers.CharField(required=False, allow_blank=True)
    responsible = serializers.CharField(required=False, allow_blank=True)
    username = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    due_date = serializers.CharField(required=False, allow_blank=True)


class EDKJiraPublishRequestSerializer(serializers.Serializer):
    """Validate the editable Jira draft while retaining the legacy error contract."""

    task = JiraTaskSerializer()
    subtasks = JiraSubtaskSerializer(many=True, required=False, default=list)

    def to_internal_value(self, data):
        task = data.get("task") if isinstance(data, Mapping) else None
        if not isinstance(task, Mapping):
            raise serializers.ValidationError({"task": ["Ana Task bilgileri zorunludur."]})
        if not str(task.get("project_key") or "").strip():
            raise serializers.ValidationError({"project_key": ["Jira proje anahtarı zorunludur."]})
        if not str(task.get("summary") or "").strip():
            raise serializers.ValidationError({"summary": ["Task özeti zorunludur."]})

        subtasks = data.get("subtasks", [])
        if not isinstance(subtasks, list):
            raise serializers.ValidationError(
                {"subtasks": ["Alt görevler liste biçiminde olmalıdır."]}
            )
        if any(not isinstance(item, Mapping) for item in subtasks):
            raise serializers.ValidationError(
                {"subtasks": ["Alt görevler nesne biçiminde olmalıdır."]}
            )
        enabled_subtasks = [item for item in subtasks if item.get("enabled", True)]
        if any(not str(item.get("summary") or "").strip() for item in enabled_subtasks):
            raise serializers.ValidationError(
                {"subtasks": ["Dahil edilen her alt görev için özet zorunludur."]}
            )
        return super().to_internal_value(data)
