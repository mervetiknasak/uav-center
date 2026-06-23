from pathlib import Path

from django.conf import settings


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".pptx", ".txt", ".csv", ".md"}


class UnsupportedDocumentError(ValueError):
    pass


def extract_text(file_path):
    path = Path(file_path)
    extension = path.suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise UnsupportedDocumentError(f"Desteklenmeyen dosya tipi: {extension}. Desteklenenler: {supported}")

    extractors = {
        ".pdf": _extract_pdf,
        ".docx": _extract_docx,
        ".xlsx": _extract_xlsx,
        ".pptx": _extract_pptx,
        ".txt": _extract_plain_text,
        ".csv": _extract_plain_text,
        ".md": _extract_plain_text,
    }
    text = extractors[extension](path)
    return _limit_text(_normalize_text(text))


def _extract_pdf(path):
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    pages = []
    for index, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        if page_text.strip():
            pages.append(f"[Sayfa {index}]\n{page_text}")
    return "\n\n".join(pages)


def _extract_docx(path):
    from docx import Document as DocxDocument

    document = DocxDocument(str(path))
    blocks = [paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()]

    for table_index, table in enumerate(document.tables, start=1):
        blocks.append(f"[Tablo {table_index}]")
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells]
            if any(cells):
                blocks.append(" | ".join(cells))

    return "\n".join(blocks)


def _extract_xlsx(path):
    from openpyxl import load_workbook

    workbook = load_workbook(filename=str(path), data_only=True, read_only=True)
    blocks = []

    for sheet in workbook.worksheets:
        blocks.append(f"[Sayfa: {sheet.title}]")
        for row in sheet.iter_rows(values_only=True):
            values = ["" if value is None else str(value) for value in row]
            if any(value.strip() for value in values):
                blocks.append(" | ".join(values))

    workbook.close()
    return "\n".join(blocks)


def _extract_pptx(path):
    from pptx import Presentation

    presentation = Presentation(str(path))
    blocks = []

    for slide_index, slide in enumerate(presentation.slides, start=1):
        blocks.append(f"[Slayt {slide_index}]")
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text.strip():
                blocks.append(shape.text.strip())

    return "\n".join(blocks)


def _extract_plain_text(path):
    for encoding in ("utf-8", "utf-8-sig", "cp1254", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(errors="ignore")


def _normalize_text(text):
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def _limit_text(text):
    max_length = getattr(settings, "DOCUMENT_MAX_TEXT_LENGTH", 120_000)
    if len(text) <= max_length:
        return text
    return text[:max_length] + "\n\n[Metin yerel işlem limiti nedeniyle kısaltıldı.]"
