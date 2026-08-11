from io import BytesIO
from pathlib import Path

from django.utils import timezone
from docxtpl import DocxTemplate

TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "templates" / "flight_permit_template.docx"


def _format_date(value):
    return value.strftime("%d.%m.%Y") if value else "-"


def _validity_status_display(permit):
    return {
        "draft": "TASLAK / DRAFT",
        "upcoming": "YAKLAŞAN / UPCOMING",
        "active": "GEÇERLİ / VALID",
        "expiring": "SÜRESİ YAKLAŞIYOR / EXPIRING",
        "expired": "SÜRESİ DOLDU / EXPIRED",
        "suspended": "ASKIYA ALINDI / SUSPENDED",
        "revoked": "İPTAL EDİLDİ / REVOKED",
    }[permit.validity_status()]


def build_flight_permit_document(permit):
    template = DocxTemplate(TEMPLATE_PATH)
    template.render(
        {
            "aircraft_number": permit.aircraft_number,
            "permit_number": permit.permit_number,
            "permit_type": permit.get_permit_type_display(),
            "issuing_authority": permit.issuing_authority,
            "flight_region": permit.flight_region or "Belirtilen operasyon sahaları",
            "valid_from": _format_date(permit.valid_from),
            "valid_until": _format_date(permit.valid_until),
            "validity_status": _validity_status_display(permit),
            "notes": permit.notes or "İzin kapsamında ilave açıklama bulunmamaktadır.",
            "generated_at": timezone.localtime().strftime("%d.%m.%Y %H:%M"),
        },
        autoescape=True,
    )
    output = BytesIO()
    template.save(output)
    output.seek(0)
    return output
