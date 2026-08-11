"""Bounded, side-effect-free preflight checks for supported document containers."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any
from zipfile import BadZipFile, LargeZipFile, ZipFile

from django.conf import settings

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
OFFICE_EXTENSIONS = {".docx", ".xlsx", ".pptx"}
SUPPORTED_EXTENSIONS = {
    ".pdf",
    *OFFICE_EXTENSIONS,
    ".txt",
    ".csv",
    ".md",
    *IMAGE_EXTENSIONS,
}

DEFAULT_MAX_ARCHIVE_ENTRIES = 2_000
DEFAULT_MAX_UNCOMPRESSED_SIZE = 100 * 1024 * 1024
DEFAULT_MAX_PDF_PAGES = 500
DEFAULT_MAX_IMAGE_FRAMES = 50
DEFAULT_MAX_IMAGE_PIXELS = 20_000_000
DEFAULT_MAX_UPLOAD_SIZE = 25 * 1024 * 1024

OOXML_REQUIRED_PARTS = {
    ".docx": {"[Content_Types].xml", "word/document.xml"},
    ".xlsx": {"[Content_Types].xml", "xl/workbook.xml"},
    ".pptx": {"[Content_Types].xml", "ppt/presentation.xml"},
}


class DocumentPreflightError(ValueError):
    """Raised when a document is malformed, encrypted, or exceeds a safe limit."""


@contextmanager
def _preserve_position(source: Any) -> Iterator[None]:
    """Restore a caller-owned file object's cursor after a read-only inspection."""

    tell = getattr(source, "tell", None)
    seek: Any = getattr(source, "seek", None)
    position = None
    if callable(tell) and callable(seek):
        try:
            position = tell()
        except (OSError, ValueError):
            position = None

    try:
        yield
    finally:
        if position is not None:
            try:
                seek(position)
            except (OSError, ValueError):
                pass


def _positive_setting(name: str, default: int) -> int:
    value = int(getattr(settings, name, default))
    if value <= 0:
        raise DocumentPreflightError(f"{name} pozitif bir değer olmalıdır.")
    return value


def validate_upload_size(size: int) -> None:
    max_upload_size = _positive_setting("DOCUMENT_MAX_UPLOAD_SIZE", DEFAULT_MAX_UPLOAD_SIZE)
    if size > max_upload_size:
        raise DocumentPreflightError("Dosya boyutu izin verilen toplam yükleme sınırını aşıyor.")


def validate_office_archive(source: Any, extension: str) -> None:
    """Validate an OOXML container without extracting any archive member."""

    normalized_extension = extension.lower()
    required_parts = OOXML_REQUIRED_PARTS.get(normalized_extension)
    if required_parts is None:
        raise DocumentPreflightError("Desteklenmeyen Office belgesi türü.")

    max_entries = _positive_setting(
        "DOCUMENT_MAX_ARCHIVE_ENTRIES",
        DEFAULT_MAX_ARCHIVE_ENTRIES,
    )
    max_uncompressed_size = _positive_setting(
        "DOCUMENT_MAX_UNCOMPRESSED_SIZE",
        DEFAULT_MAX_UNCOMPRESSED_SIZE,
    )

    try:
        with _preserve_position(source), ZipFile(source) as archive:
            entries = archive.infolist()
            if len(entries) > max_entries:
                raise DocumentPreflightError(
                    "Office belgesi izin verilen arşiv öğesi sınırını aşıyor."
                )

            names: set[str] = set()
            total_uncompressed_size = 0
            for entry in entries:
                if entry.filename in names:
                    raise DocumentPreflightError("Office belgesi yinelenen arşiv öğeleri içeriyor.")
                names.add(entry.filename)

                if entry.flag_bits & 0x1:
                    raise DocumentPreflightError("Şifreli Office belgeleri desteklenmiyor.")

                total_uncompressed_size += entry.file_size
                if total_uncompressed_size > max_uncompressed_size:
                    raise DocumentPreflightError(
                        "Office belgesi açıldığında izin verilen boyut sınırını aşıyor."
                    )

            if not required_parts.issubset(names):
                raise DocumentPreflightError("Office dosyası geçerli bir OOXML belgesi değil.")
    except DocumentPreflightError:
        raise
    except (BadZipFile, LargeZipFile, OSError, ValueError) as exc:
        raise DocumentPreflightError(
            "Office dosyası açılamadı veya geçerli bir OOXML belgesi değil."
        ) from exc


def validate_pdf_page_count(page_count: int) -> None:
    max_pages = _positive_setting("DOCUMENT_MAX_PDF_PAGES", DEFAULT_MAX_PDF_PAGES)
    if page_count > max_pages:
        raise DocumentPreflightError("PDF belgesi izin verilen sayfa sınırını aşıyor.")


def validate_pdf_document(source: Any) -> None:
    """Parse only the PDF structure needed to enforce a bounded page count."""

    from pypdf import PdfReader

    try:
        with _preserve_position(source):
            reader = PdfReader(source, strict=False)
            validate_pdf_page_count(len(reader.pages))
    except DocumentPreflightError:
        raise
    except Exception as exc:
        raise DocumentPreflightError("PDF dosyası açılamadı veya geçerli bir PDF değil.") from exc


def validate_image_dimensions(
    width: int,
    height: int,
    source_label: str = "Görsel",
) -> None:
    max_pixels = _positive_setting("OCR_MAX_PIXELS", DEFAULT_MAX_IMAGE_PIXELS)
    if width <= 0 or height <= 0:
        raise DocumentPreflightError(f"{source_label} geçerli piksel boyutlarına sahip değil.")
    if width * height > max_pixels:
        raise DocumentPreflightError(
            f"{source_label}, izin verilen sınır olan {max_pixels:,} pikseli aşıyor."
        )


def validate_image_document(source: Any) -> None:
    """Inspect image headers and frame dimensions before any pixel buffer is loaded."""

    from PIL import Image, UnidentifiedImageError

    max_frames = _positive_setting("OCR_MAX_IMAGES", DEFAULT_MAX_IMAGE_FRAMES)
    try:
        with _preserve_position(source), Image.open(source) as image:
            frame_count = int(getattr(image, "n_frames", 1))
            if frame_count > max_frames:
                raise DocumentPreflightError("Görsel izin verilen kare sınırını aşıyor.")

            for frame_index in range(frame_count):
                image.seek(frame_index)
                validate_image_dimensions(
                    *image.size,
                    source_label=f"Görsel kare {frame_index + 1}",
                )
    except DocumentPreflightError:
        raise
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError) as exc:
        raise DocumentPreflightError(
            "Görsel dosyası açılamadı veya geçerli bir görsel değil."
        ) from exc


def preflight_document(source: Any, extension: str) -> None:
    """Apply the format-specific resource checks for one supported document."""

    normalized_extension = extension.lower()
    if normalized_extension in OFFICE_EXTENSIONS:
        validate_office_archive(source, normalized_extension)
    elif normalized_extension == ".pdf":
        validate_pdf_document(source)
    elif normalized_extension in IMAGE_EXTENSIONS:
        validate_image_document(source)
