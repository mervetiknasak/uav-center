from rest_framework import serializers


class OperationalAlertThresholdsSerializer(serializers.Serializer):
    critical_days = serializers.IntegerField(min_value=0)
    horizon_days = serializers.IntegerField(min_value=0)
    stale_days = serializers.IntegerField(min_value=0)


class OperationalAlertSummarySerializer(serializers.Serializer):
    total = serializers.IntegerField(min_value=0)
    overdue = serializers.IntegerField(min_value=0)
    next_7_days = serializers.IntegerField(min_value=0)
    next_30_days = serializers.IntegerField(min_value=0)
    stale = serializers.IntegerField(min_value=0)


class OperationalAlertProjectSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    code = serializers.CharField()
    name = serializers.CharField()


class OperationalAlertPanelSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()


class OperationalAlertSerializer(serializers.Serializer):
    key = serializers.CharField()
    source_type = serializers.ChoiceField(choices=["technical_document", "flight_permit"])
    source_id = serializers.IntegerField()
    alert_type = serializers.ChoiceField(
        choices=["due_date", "review_date", "workflow_stale", "valid_until"]
    )
    bucket = serializers.ChoiceField(choices=["overdue", "next_7_days", "next_30_days", "stale"])
    date = serializers.DateField(allow_null=True)
    days_remaining = serializers.IntegerField(allow_null=True)
    days_in_status = serializers.IntegerField(allow_null=True)
    reference = serializers.CharField()
    title = serializers.CharField()
    status = serializers.CharField()
    status_display = serializers.CharField()
    priority = serializers.CharField(allow_null=True)
    project = OperationalAlertProjectSerializer(allow_null=True)
    panels = OperationalAlertPanelSerializer(many=True)
    can_notify = serializers.BooleanField()


class OperationalAlertResponseSerializer(serializers.Serializer):
    as_of = serializers.DateField()
    thresholds = OperationalAlertThresholdsSerializer()
    summary = OperationalAlertSummarySerializer()
    alerts = OperationalAlertSerializer(many=True)
