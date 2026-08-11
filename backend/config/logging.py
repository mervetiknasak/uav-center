import json
import logging
import traceback
from collections.abc import Mapping
from copy import copy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .redaction import redact_sensitive_text
from .request_context import get_request_id

REDACTED = "[REDACTED]"
SENSITIVE_NAME_PARTS = (
    "api_key",
    "authorization",
    "cookie",
    "credential",
    "password",
    "secret",
    "token",
)
STRUCTURED_FIELDS = (
    "event",
    "request_id",
    "user_id",
    "job_id",
    "document_id",
    "duration_ms",
    "http_method",
    "path",
    "status_code",
)
MAX_LOG_MESSAGE_LENGTH = 4000
MAX_TRACEBACK_FRAMES = 20


def _is_sensitive(name: str) -> bool:
    normalized = name.casefold()
    return any(part in normalized for part in SENSITIVE_NAME_PARTS)


def _redact_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            key: REDACTED if _is_sensitive(str(key)) else _redact_value(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_redact_value(item) for item in value)
    return value


def safe_exception_metadata(exc_info: Any) -> dict[str, Any]:
    """Return traceback context without exception values, source lines, or absolute paths."""

    exception_type, _exception, trace = exc_info
    frames = traceback.extract_tb(trace)[-MAX_TRACEBACK_FRAMES:] if trace else []
    return {
        "type": getattr(exception_type, "__name__", "Exception"),
        "frames": [
            {
                "file": Path(frame.filename).name,
                "line": frame.lineno,
                "function": frame.name,
            }
            for frame in frames
        ],
    }


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not getattr(record, "request_id", None):
            record.request_id = get_request_id()
        return True


class SensitiveDataFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        for name, value in tuple(record.__dict__.items()):
            if _is_sensitive(name):
                setattr(record, name, REDACTED)
            elif isinstance(value, (Mapping, list, tuple)):
                setattr(record, name, _redact_value(value))
        if record.exc_info:
            record.safe_exception = safe_exception_metadata(record.exc_info)
            record.exc_info = None
            record.exc_text = None
        return True


class SafeJsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": redact_sensitive_text(
                record.getMessage(),
                max_length=MAX_LOG_MESSAGE_LENGTH,
            ),
            "request_id": getattr(record, "request_id", get_request_id()),
        }
        for field in STRUCTURED_FIELDS:
            value = getattr(record, field, None)
            if value not in (None, ""):
                payload[field] = value
        exception = getattr(record, "safe_exception", None)
        if exception:
            payload["exception"] = exception
        return json.dumps(payload, ensure_ascii=False, default=str)


class SafeTextFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        sanitized = copy(record)
        sanitized.msg = redact_sensitive_text(
            record.getMessage(),
            max_length=MAX_LOG_MESSAGE_LENGTH,
        )
        sanitized.args = ()
        sanitized.exc_info = None
        sanitized.exc_text = None
        rendered = super().format(sanitized)
        exception = getattr(record, "safe_exception", None)
        if exception:
            rendered += " exception=" + json.dumps(exception, ensure_ascii=False)
        return rendered
