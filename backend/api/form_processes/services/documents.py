"""Render a validated record with its retained FM DOCX template."""

from datetime import date
from io import BytesIO

from django.utils import timezone
from docxtpl import DocxTemplate

from ..catalog import get_form_template


def _display_date(value) -> str:
    if not value:
        return ""
    try:
        return date.fromisoformat(value).strftime("%d.%m.%Y")
    except (TypeError, ValueError):
        return str(value)


def _template_context(record, definition) -> dict:
    context = {
        "record_number": record.record_number,
        "record_title": record.title,
        "record_status": record.get_status_display(),
        "generated_at": timezone.localdate().strftime("%d.%m.%Y"),
        **record.data,
    }
    if definition.code == "pr_qua_20_104E":
        context.update(_ssb_template_context(record.data, definition))
        return context
    if definition.code != "fm_dsg_0327":
        return context

    clearance_type = record.data.get("clearance_type")
    context.update(
        {
            "clearance_initial_mark": "☒" if clearance_type == "initial" else "☐",
            "clearance_renewal_mark": "☒" if clearance_type == "renewal" else "☐",
            "clearance_cancelled_mark": ("☒" if clearance_type == "cancelled_suspended" else "☐"),
            "valid_from_display": _display_date(record.data.get("valid_from")),
            "valid_until_display": _display_date(record.data.get("valid_until")),
        }
    )
    issue_records = []
    for row in record.data.get("issue_records") or []:
        normalized = dict(row)
        normalized["date_display"] = _display_date(row.get("date"))
        issue_records.append(normalized)
    empty_issue = {
        "issue": "",
        "date": "",
        "date_display": "",
        "prepared_by": "",
        "description": "",
    }
    context["issue_records"] = (issue_records + [empty_issue] * 5)[:5]
    return context


def _ssb_template_context(data, definition) -> dict:
    """Display values for the numbered cells of the SSB retained form."""

    def joined(*values, separator=" / "):
        return separator.join(str(value) for value in values if value)

    purpose_field = next(field for field in definition.fields if field.key == "purpose_of_flight")
    labels = dict(purpose_field.options)
    purpose = joined(
        *(labels[value] for value in data.get("purpose_of_flight", [])),
        data.get("purpose_scope"),
        separator="\n",
    )
    members = data.get("board_members") or []
    return {
        "nationality_marks_display": joined(
            data.get("aircraft_nationality"), data.get("aircraft_id_mark")
        ),
        "manufacturer_type_display": joined(
            data.get("aircraft_manufacturer"), data.get("aircraft_model")
        ),
        "flight_date_duration_display": joined(
            _display_date(data.get("intended_flight_date")),
            f"{data['flight_duration']} saat" if data.get("flight_duration") else "",
        ),
        "purpose_display": purpose,
        "issue_date_display": _display_date(data.get("issue_date")),
        "permit_issue_date_display": _display_date(data.get("permit_issue_date")),
        "validity_display": joined(
            _display_date(data.get("valid_from")),
            _display_date(data.get("valid_until")),
            separator=" – ",
        ),
        "board_member_names": [row.get("name", "") for row in members] + [""] * (4 - len(members)),
    }


def build_form_process_document(record):
    definition = get_form_template(record.template_code)
    template = DocxTemplate(definition.document_path)
    context = _template_context(record, definition)
    template.render(context, autoescape=True)
    output = BytesIO()
    template.save(output)
    output.seek(0)
    return output
