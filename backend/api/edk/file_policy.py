from pathlib import Path

from ..services.document_limits import SUPPORTED_EXTENSIONS

EDK_PRESENTATION_EXTENSIONS = frozenset(SUPPORTED_EXTENSIONS)

EDK_PRESENTATION_CONTENT_TYPES = {
    ".bmp": "image/bmp",
    ".csv": "text/csv",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".jpeg": "image/jpeg",
    ".jpg": "image/jpeg",
    ".md": "text/markdown",
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".tif": "image/tiff",
    ".tiff": "image/tiff",
    ".txt": "text/plain",
    ".webp": "image/webp",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


def presentation_content_type(filename: str) -> str:
    return EDK_PRESENTATION_CONTENT_TYPES.get(
        Path(filename).suffix.lower(),
        "application/octet-stream",
    )
