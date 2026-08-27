import json
from pathlib import Path

from rest_framework import serializers

from ..common.serializer_fields import UserDisplayNameField
from ..services.document_limits import DocumentPreflightError, preflight_document
from .catalog import (
    FORM_TEMPLATES,
    FormTemplateValidationError,
    get_form_template,
    validate_form_data,
)
from .file_policy import FORM_ATTACHMENT_EXTENSIONS, FORM_ATTACHMENT_MAX_SIZE
from .models import FormProcessRecord
from .services.lifecycle import create_form_process_record, update_form_process_record


class MultipartJSONField(serializers.JSONField):
    def to_internal_value(self, data):
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError as exc:
                raise serializers.ValidationError(
                    "Geçerli bir JSON nesnesi gönderilmelidir."
                ) from exc
        return super().to_internal_value(data)


class FormProcessRecordSerializer(serializers.ModelSerializer):
    template_code = serializers.ChoiceField(
        choices=[(template.code, template.title) for template in FORM_TEMPLATES]
    )
    process_name = serializers.SerializerMethodField()
    template_title = serializers.SerializerMethodField()
    form_number = serializers.SerializerMethodField()
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    generated_document_url = serializers.SerializerMethodField()
    created_by_name = UserDisplayNameField(source="created_by")
    updated_by_name = UserDisplayNameField(source="updated_by")
    data = MultipartJSONField(required=False)
    attachment_url = serializers.SerializerMethodField()
    remove_attachment = serializers.BooleanField(write_only=True, required=False, default=False)

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
            "attachment",
            "attachment_name",
            "attachment_content_type",
            "attachment_size",
            "attachment_url",
            "remove_attachment",
            "generated_document_url",
            "created_by_name",
            "updated_by_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "process_code",
            "attachment_name",
            "attachment_content_type",
            "attachment_size",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {"attachment": {"write_only": True, "required": False}}

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

    def validate_attachment(self, uploaded_file):
        suffix = Path(uploaded_file.name).suffix.lower()
        if suffix not in FORM_ATTACHMENT_EXTENSIONS:
            allowed = ", ".join(sorted(FORM_ATTACHMENT_EXTENSIONS))
            raise serializers.ValidationError(
                f"Desteklenmeyen doküman tipi. Desteklenenler: {allowed}"
            )
        if uploaded_file.size > FORM_ATTACHMENT_MAX_SIZE:
            raise serializers.ValidationError("Doküman boyutu 15 MB'dan büyük olamaz.")
        try:
            preflight_document(uploaded_file, suffix)
        except DocumentPreflightError as exc:
            raise serializers.ValidationError(str(exc)) from exc
        return uploaded_file

    def validate(self, attrs):
        template_code = attrs.get("template_code", getattr(self.instance, "template_code", ""))
        if self.instance and template_code != self.instance.template_code:
            raise serializers.ValidationError(
                {
                    "template_code": [
                        "Kayıt oluşturulduktan sonra süreç ve FM şablonu değiştirilemez."
                    ]
                }
            )
        data = attrs.get("data", getattr(self.instance, "data", {}))
        status_value = attrs.get(
            "status",
            getattr(self.instance, "status", FormProcessRecord.STATUS_DRAFT),
        )
        try:
            definition = get_form_template(template_code)
            attrs["data"] = validate_form_data(
                template_code,
                data,
                require_required=(status_value != FormProcessRecord.STATUS_DRAFT),
            )
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

    def get_attachment_url(self, record):
        if not record.attachment:
            return ""
        return f"/api/form-processes/{record.pk}/attachment/"

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
