import os
import re
from functools import lru_cache
from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from .document_limits import DocumentPreflightError, validate_image_dimensions

OCR_LANGUAGES = ("tr", "en")
EMAIL_PATTERN = re.compile(
    r"(?<![\w.!#$%&'*+/=?^`{|}~-])"
    r"[A-Z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?"
    r"(?:\.[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?)+",
    flags=re.IGNORECASE,
)


class OCRProcessingError(RuntimeError):
    pass


def empty_ocr_metadata(enabled=False):
    return {
        "enabled": enabled,
        "engine": "easyocr" if enabled else None,
        "languages": list(OCR_LANGUAGES) if enabled else [],
        "processed_images": 0,
        "processed_pages": 0,
        "email_addresses": [],
        "warnings": [],
    }


@lru_cache(maxsize=1)
def get_reader():
    model_directory = Path(settings.OCR_MODEL_DIR)
    model_directory.mkdir(parents=True, exist_ok=True)
    allow_download = getattr(settings, "OCR_ALLOW_MODEL_DOWNLOAD", False)
    required_models = ("craft_mlt_25k.pth", "latin_g2.pth")
    missing_models = [name for name in required_models if not (model_directory / name).is_file()]
    if missing_models and not allow_download:
        raise OCRProcessingError(
            "EasyOCR model dosyaları bulunamadı: "
            f"{', '.join(missing_models)}. Modelleri {model_directory} dizinine yerleştirin "
            "veya hazırlık sırasında OCR_ALLOW_MODEL_DOWNLOAD=true kullanın."
        )

    try:
        import certifi
        import easyocr
    except ImportError as exc:
        raise OCRProcessingError(
            "EasyOCR kurulu değil. 'pip install -r requirements.txt' komutunu çalıştırın."
        ) from exc

    # macOS framework Python installations may not expose a CA bundle to urllib.
    # Respect an operator-provided certificate path; otherwise use Certifi's bundle.
    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
    try:
        return easyocr.Reader(
            list(OCR_LANGUAGES),
            gpu=getattr(settings, "OCR_USE_GPU", False),
            model_storage_directory=str(model_directory),
            download_enabled=allow_download,
        )
    except Exception as exc:
        download_hint = (
            "Model indirmeye izin vermek için OCR_ALLOW_MODEL_DOWNLOAD=true kullanın veya "
            f"EasyOCR modellerini {model_directory} dizinine önceden yerleştirin."
        )
        raise OCRProcessingError(
            f"EasyOCR modeli yüklenemedi. {download_hint} Ayrıntı: {exc}"
        ) from exc


def read_image(image, source_label):
    """Return normalized OCR text for a Pillow image after resource checks."""
    try:
        width, height = image.size
        validate_image_dimensions(width, height, source_label=source_label)
    except DocumentPreflightError as exc:
        raise OCRProcessingError(str(exc)) from exc

    try:
        import numpy as np

        prepared = image.convert("RGB")
        lines = get_reader().readtext(np.asarray(prepared), detail=0, paragraph=False)
    except OCRProcessingError:
        raise
    except Exception as exc:
        raise OCRProcessingError(f"{source_label} OCR ile okunamadı: {exc}") from exc

    return normalize_ocr_text("\n".join(str(line) for line in lines if str(line).strip()))


def open_image_bytes(content):
    from PIL import Image

    image = Image.open(BytesIO(content))
    try:
        width, height = image.size
        validate_image_dimensions(width, height)
        image.load()
    except DocumentPreflightError as exc:
        image.close()
        raise OCRProcessingError(str(exc)) from exc
    except Exception:
        image.close()
        raise
    return image


def normalize_ocr_text(text):
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def extract_email_addresses(text):
    addresses = []
    seen = set()
    for match in EMAIL_PATTERN.finditer(text or ""):
        candidate = match.group(0).strip(".,;:!?()[]{}<>\"'").lower()
        try:
            validate_email(candidate)
        except ValidationError:
            continue
        if candidate not in seen:
            seen.add(candidate)
            addresses.append(candidate)
    return addresses
