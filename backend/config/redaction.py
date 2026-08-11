"""Framework-independent redaction shared by API and logging boundaries."""

import re

DEFAULT_SAFE_ERROR_MAX_LENGTH = 1000
REDACTED_SECRET = "[REDACTED]"  # noqa: S105 - fixed masking marker, not a credential.
REDACTED_URL = "[REDACTED_URL]"
REDACTED_PATH = "[REDACTED_PATH]"
REDACTED_EMAIL = "[REDACTED_EMAIL]"

_BEARER_TOKEN = re.compile(r"(?i)\bBearer\s+[^\s,;]+")
_SECRET_ASSIGNMENT = re.compile(
    r"(?i)\b(password|passwd|token|secret|api[_ -]?key|authorization)\b"
    r"(\s*(?:[:=]|\bis\b)\s*)"
    r'(?:"[^"]*"|\'[^\']*\'|[^\s,;]+)'
)
_JWT = re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b")
_URL = re.compile(r'(?i)\b(?:https?|ftp|file)://[^\s<>"\']+')
_INTERNAL_HOST = re.compile(
    r"(?i)\b(?:"
    r"localhost|127(?:\.\d{1,3}){3}|10(?:\.\d{1,3}){3}|"
    r"192\.168(?:\.\d{1,3}){2}|172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2}|"
    r"[A-Za-z0-9.-]+\.(?:internal|local)"
    r")(?:\:\d{1,5})?(?:/[^\s<>\"']*)?"
)
_EMAIL = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
_QUOTED_ABSOLUTE_PATH = re.compile(
    r"(?P<quote>[\"'])(?:(?:[A-Za-z]:[\\/])|/|\\\\)[^\"'\r\n]+(?P=quote)"
)
_WINDOWS_ABSOLUTE_PATH = re.compile(
    r"(?i)(?<![\w])(?:"
    r"[A-Z]:[\\/](?:[^\\/\s,;]+[\\/])*[^\\/\s,;]*|"
    r"\\\\[^\\/\s,;]+[\\/][^\\/\s,;]+(?:[\\/][^\\/\s,;]+)*"
    r")"
)
_POSIX_ABSOLUTE_PATH = re.compile(r"(?<![:\w])/(?:[\w.@%+~=-]+/)*[\w.@%+~=-]+")


def redact_sensitive_text(value, *, max_length: int = DEFAULT_SAFE_ERROR_MAX_LENGTH) -> str:
    """Return bounded single-line text with infrastructure and PII removed."""

    if max_length < 0:
        raise ValueError("max_length negatif olamaz.")
    text = " ".join(str(value).splitlines()).strip()
    text = _BEARER_TOKEN.sub(f"Bearer {REDACTED_SECRET}", text)
    text = _SECRET_ASSIGNMENT.sub(rf"\1\2{REDACTED_SECRET}", text)
    text = _JWT.sub(REDACTED_SECRET, text)
    text = _URL.sub(REDACTED_URL, text)
    text = _INTERNAL_HOST.sub(REDACTED_URL, text)
    text = _EMAIL.sub(REDACTED_EMAIL, text)
    text = _QUOTED_ABSOLUTE_PATH.sub(REDACTED_PATH, text)
    text = _WINDOWS_ABSOLUTE_PATH.sub(REDACTED_PATH, text)
    text = _POSIX_ABSOLUTE_PATH.sub(REDACTED_PATH, text)
    return text[:max_length]


def safe_exception_message(
    exc: BaseException,
    *,
    max_length: int = DEFAULT_SAFE_ERROR_MAX_LENGTH,
) -> str:
    """Build a bounded audit message without exposing exception payload secrets."""

    if max_length < 0:
        raise ValueError("max_length negatif olamaz.")
    prefix = f"{exc.__class__.__name__}: "
    detail = str(exc).strip() or "Ayrıntı sağlanmadı."
    available_length = max(0, max_length - len(prefix))
    safe_detail = redact_sensitive_text(detail, max_length=available_length)
    return f"{prefix}{safe_detail}"[:max_length]
