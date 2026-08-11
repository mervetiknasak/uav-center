from rest_framework import serializers

from .models import AsyncJob


class AsyncJobSerializer(serializers.ModelSerializer):
    job_type_display = serializers.CharField(source="get_job_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    document_name = serializers.CharField(source="document.original_name", read_only=True)

    class Meta:
        model = AsyncJob
        fields = [
            "id",
            "job_type",
            "job_type_display",
            "status",
            "status_display",
            "priority",
            "progress",
            "result",
            "error_message",
            "attempts",
            "max_attempts",
            "document",
            "document_name",
            "created_at",
            "started_at",
            "completed_at",
            "updated_at",
        ]
        read_only_fields = fields
