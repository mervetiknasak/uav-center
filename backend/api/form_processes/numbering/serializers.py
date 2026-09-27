from django.db import transaction
from rest_framework import serializers

from ..models import FormNumberingConfigLock, FormNumberMapping
from . import client
from .rules import validate_mapping, validate_no_cycles


class MappingSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormNumberMapping
        fields = [
            "id",
            "template_code",
            "target_field",
            "format_code",
            "enabled",
            "context_sources",
            "format_snapshot",
            "updated_at",
        ]
        read_only_fields = ["format_snapshot", "updated_at"]

    def validate(self, attrs):
        def value(name):
            return attrs.get(name, getattr(self.instance, name, None))

        if self.instance and any(
            value(name) != getattr(self.instance, name)
            for name in ("template_code", "target_field")
        ):
            raise serializers.ValidationError(
                "Mevcut eşleştirmenin formu ve hedef alanı değiştirilemez; yeni eşleştirme oluşturun."
            )
        if (
            self.instance
            and value("enabled") is False
            and value("format_code") == self.instance.format_code
        ):
            contract = self.instance.format_snapshot
        else:
            contract = client.get_format(value("format_code"))
        validate_mapping(
            value("template_code"), value("target_field"), value("context_sources"), contract
        )
        attrs["format_snapshot"] = contract
        return attrs

    def save(self, **kwargs):
        with transaction.atomic():
            template_code = self.validated_data.get(
                "template_code", getattr(self.instance, "template_code", "")
            )
            lock, _ = FormNumberingConfigLock.objects.get_or_create(template_code=template_code)
            # A real UPDATE serializes configuration writes on SQLite as well as PostgreSQL.
            FormNumberingConfigLock.objects.filter(pk=lock.pk).update(template_code=template_code)
            result = super().save(**kwargs)
            validate_no_cycles(FormNumberMapping.objects.filter(template_code=template_code))
            return result


class AllocationInputSerializer(serializers.Serializer):
    mapping_id = serializers.IntegerField(min_value=1)
    record_id = serializers.IntegerField(min_value=1, required=False, allow_null=True)
    expected_updated_at = serializers.DateTimeField(required=False, allow_null=True)
    form = serializers.JSONField()
    manual_context = serializers.JSONField(default=dict)

    def validate_form(self, value):
        if not isinstance(value, dict) or set(value) - {
            "template_code",
            "record_number",
            "title",
            "data",
            "notes",
            "remove_attachment",
        }:
            raise serializers.ValidationError("Geçersiz form verisi.")
        return value
