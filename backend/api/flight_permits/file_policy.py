"""Server-owned upload policy for flight-permit documents."""

from pathlib import Path

DOCUMENT_CONTENT_TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}
FLIGHT_PERMIT_DOCUMENT_EXTENSIONS = frozenset(DOCUMENT_CONTENT_TYPES)
FLIGHT_PERMIT_DOCUMENT_MAX_SIZE = 15 * 1024 * 1024


def document_content_type(filename: str) -> str:
    """Resolve deterministic MIME without trusting client-provided metadata."""

    return DOCUMENT_CONTENT_TYPES.get(
        Path(filename).suffix.lower(),
        "application/octet-stream",
    )
