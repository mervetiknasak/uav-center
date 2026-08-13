"""Flight-permit sub-template catalog and template-owned field validation."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

TEMPLATE_DIRECTORY = Path(__file__).resolve().parent.parent / "templates"


@dataclass(frozen=True)
class TemplateField:
    key: str
    label: str
    required: bool = False
    multiline: bool = False
    max_length: int = 500
    placeholder: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "label": self.label,
            "required": self.required,
            "type": "textarea" if self.multiline else "text",
            "max_length": self.max_length,
            "placeholder": self.placeholder,
        }


@dataclass(frozen=True)
class FlightPermitTemplate:
    code: str
    institution: str
    description: str
    document_path: Path
    fields: tuple[TemplateField, ...]
    append_field_summary: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "institution": self.institution,
            "description": self.description,
            "fields": [field.as_dict() for field in self.fields],
        }


FLIGHT_PERMIT_TEMPLATES = (
    FlightPermitTemplate(
        code="institution_a",
        institution="A Kurumu",
        description="A Kurumuna gönderilecek uçuş izni şablonu.",
        document_path=TEMPLATE_DIRECTORY / "flight_permit_template.docx",
        fields=(
            TemplateField(
                "contract_number",
                "Sözleşme numarası",
                max_length=120,
                placeholder="Örn. SÖZ-2026-104",
            ),
            TemplateField(
                "flight_test_plan_number",
                "Uçuş test planı numarası",
                max_length=120,
                placeholder="Örn. FTP-2026-18",
            ),
        ),
    ),
    FlightPermitTemplate(
        code="institution_b",
        institution="B Kurumu",
        description="B Kurumuna gönderilecek kurul onaylı uçuş izni şablonu.",
        document_path=TEMPLATE_DIRECTORY / "flight_permit_template_old.docx",
        fields=(
            TemplateField(
                "approval_reference",
                "Kurul onay referansı",
                required=True,
                max_length=120,
                placeholder="Örn. KURUL-2026/42",
            ),
            TemplateField(
                "approving_authority",
                "Onaylayan makam",
                max_length=200,
                placeholder="Onaylayan birim veya makam",
            ),
        ),
    ),
    FlightPermitTemplate(
        code="institution_c",
        institution="C Kurumu",
        description="C Kurumuna gönderilecek operasyon koordinasyon şablonu.",
        document_path=TEMPLATE_DIRECTORY / "flight_permit_template_c.docx",
        fields=(
            TemplateField(
                "coordination_contact",
                "Koordinasyon sorumlusu",
                required=True,
                max_length=200,
                placeholder="Ad soyad / birim",
            ),
            TemplateField(
                "coordination_reference",
                "Koordinasyon referansı",
                max_length=120,
                placeholder="Örn. KR-2026-08",
            ),
            TemplateField(
                "operational_notes",
                "Kuruma özel operasyon notları",
                multiline=True,
                max_length=2000,
                placeholder="Koordinasyon ve operasyon ayrıntıları",
            ),
        ),
        append_field_summary=False,
    ),
)

FLIGHT_PERMIT_TEMPLATE_BY_CODE = {template.code: template for template in FLIGHT_PERMIT_TEMPLATES}
DEFAULT_FLIGHT_PERMIT_TEMPLATE_CODE = FLIGHT_PERMIT_TEMPLATES[0].code


class TemplateDataValidationError(ValueError):
    def __init__(self, errors: dict[str, list[str]]):
        super().__init__("Şablona özgü alanlar geçersiz.")
        self.errors = errors


def get_flight_permit_template(code: str) -> FlightPermitTemplate:
    try:
        return FLIGHT_PERMIT_TEMPLATE_BY_CODE[code]
    except KeyError as exc:
        raise TemplateDataValidationError(
            {"template_code": ["Geçerli bir uçuş izni şablonu seçilmelidir."]}
        ) from exc


def validate_template_data(code: str, data: Any) -> dict[str, str]:
    template = get_flight_permit_template(code)
    if not isinstance(data, dict):
        raise TemplateDataValidationError(
            {"template_data": ["Şablona özgü alanlar nesne biçiminde gönderilmelidir."]}
        )

    field_by_key = {field.key: field for field in template.fields}
    errors: dict[str, list[str]] = {}
    unknown_fields = sorted(set(data) - set(field_by_key))
    if unknown_fields:
        errors["template_data"] = [
            f"Seçilen şablonda bulunmayan alanlar gönderildi: {', '.join(unknown_fields)}"
        ]

    cleaned: dict[str, str] = {}
    for key, field in field_by_key.items():
        raw_value = data.get(key, "")
        if not isinstance(raw_value, str):
            errors[key] = ["Metin değeri gönderilmelidir."]
            continue
        value = raw_value.strip()
        if field.required and not value:
            errors[key] = [f"{field.label} zorunludur."]
        elif len(value) > field.max_length:
            errors[key] = [f"En fazla {field.max_length} karakter girilebilir."]
        cleaned[key] = value

    if errors:
        raise TemplateDataValidationError(errors)
    return cleaned


def flight_permit_template_catalog() -> list[dict[str, Any]]:
    return [template.as_dict() for template in FLIGHT_PERMIT_TEMPLATES]
