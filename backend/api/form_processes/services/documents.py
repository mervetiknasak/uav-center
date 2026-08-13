"""Render a validated record with its retained FM DOCX template."""

from io import BytesIO

from django.utils import timezone
from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.table import Table
from docxtpl import DocxTemplate

from ..catalog import get_form_template


def _set_cell_shading(cell, fill: str) -> None:
    properties = cell._tc.get_or_add_tcPr()
    shading = properties.find(qn("w:shd"))
    if shading is None:
        shading = OxmlElement("w:shd")
        properties.append(shading)
    shading.set(qn("w:fill"), fill)


def _set_table_borders(table) -> None:
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        border = OxmlElement(f"w:{edge}")
        border.set(qn("w:val"), "single")
        border.set(qn("w:sz"), "5")
        border.set(qn("w:color"), "B7C6D8")
        borders.append(border)
    table._tbl.tblPr.append(borders)


def _display_value(value) -> str:
    if value is True:
        return "Evet"
    if value is False:
        return "Hayır"
    return str(value or "—")


def build_form_process_document(record):
    definition = get_form_template(record.template_code)
    template = DocxTemplate(definition.document_path)
    context = {
        "record_number": record.record_number,
        "record_title": record.title,
        "record_status": record.get_status_display(),
        "generated_at": timezone.localdate().strftime("%d.%m.%Y"),
        **record.data,
    }
    template.render(context, autoescape=True)
    rendered = BytesIO()
    template.save(rendered)
    rendered.seek(0)

    document = Document(rendered)
    document.add_page_break()
    heading = document.add_paragraph()
    heading.paragraph_format.keep_with_next = True
    heading.add_run("SÜREÇ KAYIT BİLGİLERİ").bold = True
    metadata = document.add_table(rows=0, cols=2)
    _set_table_borders(metadata)
    metadata_rows = (
        ("Süreç", definition.process_name),
        ("Form", f"{definition.form_number} — {definition.title}"),
        ("Kayıt numarası", record.record_number),
        ("Kayıt başlığı", record.title),
        ("Durum", record.get_status_display()),
        ("Oluşturma tarihi", timezone.localtime(record.created_at).strftime("%d.%m.%Y %H:%M")),
        ("Son güncelleyen", getattr(record.updated_by, "username", "") or "—"),
    )
    for label, value in metadata_rows:
        cells = metadata.add_row().cells
        _set_cell_shading(cells[0], "E8EEF6")
        cells[0].text = label
        cells[1].text = _display_value(value)
        for cell in cells:
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER

    current_group = None
    details: Table | None = None
    for field in definition.fields:
        if field.group != current_group:
            current_group = field.group
            group_heading = document.add_paragraph()
            group_heading.paragraph_format.keep_with_next = True
            group_heading.add_run(current_group).bold = True
            details = document.add_table(rows=0, cols=2)
            _set_table_borders(details)
        if details is None:
            raise RuntimeError("Form alan grubu tablosu oluşturulamadı.")
        cells = details.add_row().cells
        _set_cell_shading(cells[0], "F1F5F9")
        cells[0].text = field.label
        cells[1].text = _display_value(record.data.get(field.key))
        for cell in cells:
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER

    if record.notes:
        notes_heading = document.add_paragraph()
        notes_heading.add_run("Notlar").bold = True
        document.add_paragraph(record.notes)

    output = BytesIO()
    document.save(output)
    output.seek(0)
    return output
