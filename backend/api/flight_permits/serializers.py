import json
from pathlib import Path

from rest_framework import serializers
from rest_framework.fields import empty
from rest_framework.utils import html

from ..services.document_limits import DocumentPreflightError, preflight_document
from .file_policy import (
    FLIGHT_PERMIT_DOCUMENT_EXTENSIONS,
    FLIGHT_PERMIT_DOCUMENT_MAX_SIZE,
)
from .models import FlightPermit
from .purposes import FlightPurpose, flight_purpose_labels
from .services.lifecycle import create_flight_permit, update_flight_permit


class MultipartChoiceListField(serializers.ListField):
    def get_value(self, dictionary):
        if html.is_html_input(dictionary):
            return dictionary.get(self.field_name, empty)
        return super().get_value(dictionary)

    def to_internal_value(self, data):
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError as exc:
                raise serializers.ValidationError(
                    "Geçerli bir seçim listesi gönderilmelidir."
                ) from exc
        return super().to_internal_value(data)


class FlightPermitSerializer(serializers.ModelSerializer):
    purpose_of_flight = MultipartChoiceListField(
        child=serializers.ChoiceField(choices=FlightPurpose.choices),
        required=False,
        allow_empty=True,
        max_length=len(FlightPurpose.choices),
    )
    purpose_of_flight_display = serializers.SerializerMethodField()
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    validity_status = serializers.SerializerMethodField()
    validity_status_display = serializers.SerializerMethodField()
    document_url = serializers.SerializerMethodField()
    generated_document_url = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source="created_by.username", read_only=True)
    updated_by_name = serializers.CharField(source="updated_by.username", read_only=True)
    remove_document = serializers.BooleanField(write_only=True, required=False, default=False)

    class Meta:
        model = FlightPermit
        fields = [
            "id",
            "permit_applicant",
            "permit_number",
            "aircraft_nationality",
            "aircraft_id_mark",
            "aircraft_owner",
            "aircraft_type",
            "aircraft_manufacturer",
            "serial_number",
            "purpose_of_flight",
            "purpose_of_flight_display",
            "target_date",
            "flight_duration",
            "aircraft_configuration",
            "conditions_restrictions",
            "conditions_substantiations",
            "is_recommendation",
            "valid_from",
            "valid_until",
            "status",
            "status_display",
            "validity_status",
            "validity_status_display",
            "notes",
            "document",
            "document_name",
            "document_content_type",
            "document_size",
            "document_url",
            "generated_document_url",
            "remove_document",
            "created_by_name",
            "updated_by_name",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {"document": {"write_only": True, "required": False}}
        read_only_fields = [
            "document_name",
            "document_content_type",
            "document_size",
            "created_at",
            "updated_at",
        ]

    def validate_permit_number(self, value):
        return value.strip().upper()

    def validate_permit_applicant(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Başvuru sahibi zorunludur.")
        return value

    def validate_aircraft_nationality(self, value):
        return value.strip().upper()

    def validate_aircraft_id_mark(self, value):
        return value.strip().upper()

    def validate_serial_number(self, value):
        return value.strip().upper()

    def validate_purpose_of_flight(self, value):
        if len(value) != len(set(value)):
            raise serializers.ValidationError("Aynı uçuş amacı birden fazla kez seçilemez.")
        return value

    def validate_document(self, uploaded_file):
        suffix = Path(uploaded_file.name).suffix.lower()
        if suffix not in FLIGHT_PERMIT_DOCUMENT_EXTENSIONS:
            allowed = ", ".join(sorted(FLIGHT_PERMIT_DOCUMENT_EXTENSIONS))
            raise serializers.ValidationError(
                f"Desteklenmeyen doküman tipi. Desteklenenler: {allowed}"
            )
        if uploaded_file.size > FLIGHT_PERMIT_DOCUMENT_MAX_SIZE:
            raise serializers.ValidationError("Doküman boyutu 15 MB'dan büyük olamaz.")
        try:
            preflight_document(uploaded_file, suffix)
        except DocumentPreflightError as exc:
            raise serializers.ValidationError(str(exc)) from exc
        return uploaded_file

    def validate(self, attrs):
        valid_from = attrs.get("valid_from", getattr(self.instance, "valid_from", None))
        valid_until = attrs.get("valid_until", getattr(self.instance, "valid_until", None))
        if valid_from and valid_until and valid_until < valid_from:
            raise serializers.ValidationError(
                {"valid_until": ["Geçerlilik bitiş tarihi başlangıç tarihinden önce olamaz."]}
            )
        return attrs

    def get_validity_status(self, permit):
        return permit.validity_status()

    def get_purpose_of_flight_display(self, permit):
        return flight_purpose_labels(permit.purpose_of_flight)

    def get_validity_status_display(self, permit):
        return {
            "draft": "Taslak",
            "upcoming": "Yaklaşan",
            "active": "Geçerli",
            "expiring": "Süresi Yaklaşıyor",
            "expired": "Süresi Doldu",
            "suspended": "Askıya Alındı",
            "revoked": "İptal Edildi",
        }[self.get_validity_status(permit)]

    def get_document_url(self, permit):
        if not permit.document:
            return ""
        return f"/api/flight-permits/{permit.pk}/document/"

    def get_generated_document_url(self, permit):
        return f"/api/flight-permits/{permit.pk}/generated-document/"

    def create(self, validated_data):
        return create_flight_permit(
            validated_data=validated_data,
            actor=self.context["request"].user,
        )

    def update(self, instance, validated_data):
        return update_flight_permit(
            permit=instance,
            validated_data=validated_data,
            actor=self.context["request"].user,
        )
