"""Server-owned upload policy for engineering form attachments."""

from pathlib import Path

FORM_ATTACHMENT_CONTENT_TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}
FORM_ATTACHMENT_EXTENSIONS = frozenset(FORM_ATTACHMENT_CONTENT_TYPES)
FORM_ATTACHMENT_MAX_SIZE = 15 * 1024 * 1024


def attachment_content_type(filename: str) -> str:
    """Resolve deterministic MIME without trusting client-provided metadata."""

    return FORM_ATTACHMENT_CONTENT_TYPES.get(
        Path(filename).suffix.lower(),
        "application/octet-stream",
    )
