"""Request DTOs for meeting-minutes HTTP use cases."""

from collections.abc import Mapping

from rest_framework import serializers


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


class WordToJiraPublishRequestSerializer(serializers.Serializer):
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
