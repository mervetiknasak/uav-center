from pathlib import Path

from rest_framework import serializers

from ..services.document_extractor import IMAGE_EXTENSIONS, SUPPORTED_EXTENSIONS
from ..services.document_limits import (
    DocumentPreflightError,
    preflight_document,
    validate_upload_size,
)
from .models import AnalysisControl, Document, DocumentAnalysisRun


class DocumentListSerializer(serializers.ModelSerializer):
    text_length = serializers.SerializerMethodField()
    owner_id = serializers.IntegerField(read_only=True, allow_null=True)
    owner_name = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            "id",
            "original_name",
            "content_type",
            "size",
            "owner_id",
            "owner_name",
            "prompt",
            "status",
            "ai_result",
            "error_message",
            "created_at",
            "processed_at",
            "text_length",
        ]
        read_only_fields = fields

    def get_text_length(self, document):
        return len(document.extracted_text or "")

    def get_owner_name(self, document):
        return document.owner.username if document.owner_id else None


class DocumentDetailSerializer(DocumentListSerializer):
    class Meta(DocumentListSerializer.Meta):
        fields = DocumentListSerializer.Meta.fields + ["extracted_text"]


class DocumentUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    prompt = serializers.CharField(
        trim_whitespace=True,
        allow_blank=True,
        required=False,
        default="",
        max_length=8000,
    )
    use_ocr = serializers.BooleanField(default=False)
    use_ai = serializers.BooleanField(default=True)

    def validate_file(self, uploaded_file):
        suffix = ""
        if "." in uploaded_file.name:
            suffix = "." + uploaded_file.name.rsplit(".", 1)[-1].lower()

        if suffix not in SUPPORTED_EXTENSIONS:
            supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
            raise serializers.ValidationError(
                f"Desteklenmeyen dosya tipi. Desteklenenler: {supported}"
            )

        try:
            validate_upload_size(uploaded_file.size)
            preflight_document(uploaded_file, suffix)
        except DocumentPreflightError as exc:
            raise serializers.ValidationError(str(exc)) from exc

        return uploaded_file

    def validate(self, attrs):
        if attrs["use_ai"] and not attrs["prompt"]:
            raise serializers.ValidationError(
                {"prompt": ["AI ile işlemek için prompt zorunludur."]}
            )

        suffix = Path(attrs["file"].name).suffix.lower()
        if suffix in IMAGE_EXTENSIONS and not attrs["use_ocr"]:
            raise serializers.ValidationError(
                {"use_ocr": ["Resim dosyalarından metin çıkarmak için OCR etkinleştirilmelidir."]}
            )
        return attrs


class AnalysisControlSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    database_id = serializers.IntegerField(source="pk", read_only=True)
    kind = serializers.SerializerMethodField()

    class Meta:
        model = AnalysisControl
        fields = [
            "id",
            "database_id",
            "name",
            "description",
            "instructions",
            "severity",
            "is_active",
            "kind",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def get_id(self, control):
        return f"custom:{control.pk}"

    def get_kind(self, _control):
        return "custom"

    def validate_name(self, value):
        return value.strip()

    def validate_instructions(self, value):
        value = value.strip()
        if len(value) < 10:
            raise serializers.ValidationError("Kontrol talimatı en az 10 karakter olmalıdır.")
        return value

    def validate(self, attrs):
        request = self.context.get("request")
        owner = getattr(request, "user", None)
        name = attrs.get("name", getattr(self.instance, "name", ""))
        duplicate = AnalysisControl.objects.filter(owner=owner, name__iexact=name)
        if self.instance:
            duplicate = duplicate.exclude(pk=self.instance.pk)
        if duplicate.exists():
            raise serializers.ValidationError({"name": ["Bu isimde bir kontrol zaten var."]})
        return attrs


class DocumentRagQuerySerializer(serializers.Serializer):
    query = serializers.CharField(trim_whitespace=True, min_length=2, max_length=8000)
    top_k = serializers.IntegerField(required=False, default=6, min_value=1, max_value=12)


class DocumentControlRunSerializer(serializers.Serializer):
    control_ids = serializers.ListField(
        child=serializers.CharField(max_length=80),
        required=False,
        default=list,
        max_length=10,
    )


class DocumentAnalysisRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentAnalysisRun
        fields = [
            "id",
            "document",
            "query",
            "status",
            "controls",
            "result",
            "error_message",
            "created_at",
            "completed_at",
        ]
        read_only_fields = fields
