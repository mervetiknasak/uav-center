"""Compatibility façade for the project-level redaction utilities."""

from config.redaction import (
    DEFAULT_SAFE_ERROR_MAX_LENGTH,
    REDACTED_EMAIL,
    REDACTED_PATH,
    REDACTED_SECRET,
    REDACTED_URL,
    redact_sensitive_text,
    safe_exception_message,
)

__all__ = [
    "DEFAULT_SAFE_ERROR_MAX_LENGTH",
    "REDACTED_EMAIL",
    "REDACTED_PATH",
    "REDACTED_SECRET",
    "REDACTED_URL",
    "redact_sensitive_text",
    "safe_exception_message",
]
