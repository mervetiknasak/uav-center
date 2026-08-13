from rest_framework import serializers

from .catalog import (
    FORM_TEMPLATES,
    FormTemplateValidationError,
    get_form_template,
    validate_form_data,
)
from .models import FormProcessRecord
from .services.lifecycle import create_form_process_record, update_form_process_record


class FormProcessRecordSerializer(serializers.ModelSerializer):
    template_code = serializers.ChoiceField(
        choices=[(template.code, template.title) for template in FORM_TEMPLATES]
    )
    process_name = serializers.SerializerMethodField()
    template_title = serializers.SerializerMethodField()
    form_number = serializers.SerializerMethodField()
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    generated_document_url = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source="created_by.username", read_only=True)
    updated_by_name = serializers.CharField(source="updated_by.username", read_only=True)

    class Meta:
        model = FormProcessRecord
        fields = [
            "id",
            "process_code",
            "process_name",
            "template_code",
            "template_title",
            "form_number",
            "record_number",
            "title",
            "status",
            "status_display",
            "data",
            "notes",
            "generated_document_url",
            "created_by_name",
            "updated_by_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "process_code",
            "created_at",
            "updated_at",
        ]

    def validate_record_number(self, value):
        value = value.strip().upper()
        if not value:
            raise serializers.ValidationError("Kayıt numarası zorunludur.")
        return value

    def validate_title(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Kayıt başlığı zorunludur.")
        return value

    def validate(self, attrs):
        template_code = attrs.get("template_code", getattr(self.instance, "template_code", ""))
        data = attrs.get("data", getattr(self.instance, "data", {}))
        try:
            definition = get_form_template(template_code)
            attrs["data"] = validate_form_data(template_code, data)
        except FormTemplateValidationError as exc:
            raise serializers.ValidationError(exc.errors) from exc
        attrs["process_code"] = definition.process_code
        record_number = attrs.get(
            "record_number",
            getattr(self.instance, "record_number", ""),
        )
        duplicate = FormProcessRecord.objects.filter(
            process_code=definition.process_code,
            record_number=record_number,
        )
        if self.instance:
            duplicate = duplicate.exclude(pk=self.instance.pk)
        if duplicate.exists():
            raise serializers.ValidationError(
                {"record_number": ["Bu süreçte aynı kayıt numarası zaten kullanılıyor."]}
            )
        return attrs

    def _definition(self, record):
        return get_form_template(record.template_code)

    def get_process_name(self, record):
        return self._definition(record).process_name

    def get_template_title(self, record):
        return self._definition(record).title

    def get_form_number(self, record):
        return self._definition(record).form_number

    def get_generated_document_url(self, record):
        return f"/api/form-processes/{record.pk}/generated-document/"

    def create(self, validated_data):
        return create_form_process_record(
            validated_data=validated_data,
            actor=self.context["request"].user,
        )

    def update(self, instance, validated_data):
        return update_form_process_record(
            record=instance,
            validated_data=validated_data,
            actor=self.context["request"].user,
        )
