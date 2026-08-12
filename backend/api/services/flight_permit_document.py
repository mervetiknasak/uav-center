from io import BytesIO
from pathlib import Path

from docxtpl import DocxTemplate

from ..flight_permits.purposes import flight_purpose_labels

TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "templates" / "flight_permit_template.docx"


def _format_date(value):
    return value.strftime("%d.%m.%Y") if value else "-"


def _join_values(*values):
    return " / ".join(str(value).strip() for value in values if str(value or "").strip()) or "-"


def _target_date_and_duration(permit):
    duration = f"{permit.flight_duration} saat" if permit.flight_duration else ""
    return _join_values(_format_date(permit.target_date) if permit.target_date else "", duration)


def build_flight_permit_document(permit):
    template = DocxTemplate(TEMPLATE_PATH)
    template.render(
        {
            "permit_applicant": permit.permit_applicant,
            "permit_number": permit.permit_number,
            "aircraft_nationality": _join_values(
                permit.aircraft_nationality,
                permit.aircraft_id_mark,
            ),
            "aircraft_id_mark": "",
            "aircraft_owner": permit.aircraft_owner or "-",
            "aircraft_manufacturer": _join_values(
                permit.aircraft_manufacturer,
                permit.aircraft_type,
            ),
            "aircraft_type": "",
            "serial_number": permit.serial_number or "-",
            "purpose_of_flight": "  •  ".join(flight_purpose_labels(permit.purpose_of_flight))
            or "-",
            "target_date": _target_date_and_duration(permit),
            "flight_duration": "",
            "aircraft_configuration": permit.aircraft_configuration or "-",
            "conditions_restrictions": permit.conditions_restrictions or "-",
            "conditions_substantiations": permit.conditions_substantiations or "-",
            "is_recommendation": permit.is_recommendation,
            "valid_from": _format_date(permit.valid_from),
            "valid_until": _format_date(permit.valid_until),
        },
        autoescape=True,
    )
    output = BytesIO()
    template.save(output)
    output.seek(0)
    return output
