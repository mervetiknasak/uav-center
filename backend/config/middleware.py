import logging
import re
import sys
import uuid
from collections.abc import Callable
from time import perf_counter

from django.http import HttpRequest, HttpResponse

from .logging import safe_exception_metadata
from .request_context import reset_request_id, set_request_id

REQUEST_ID_HEADER = "X-Request-ID"
REQUEST_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")
logger = logging.getLogger("config.request")


def _request_id_from(request: HttpRequest) -> str:
    candidate = request.headers.get(REQUEST_ID_HEADER, "").strip()
    if REQUEST_ID_PATTERN.fullmatch(candidate):
        return candidate
    return uuid.uuid4().hex


class RequestIdMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request_id = _request_id_from(request)
        request.request_id = request_id
        token = set_request_id(request_id)
        started_at = perf_counter()
        try:
            try:
                response = self.get_response(request)
            except Exception:
                self._log_completion(
                    request,
                    500,
                    started_at,
                    safe_exception=safe_exception_metadata(sys.exc_info()),
                )
                raise

            response[REQUEST_ID_HEADER] = request_id
            self._log_completion(request, response.status_code, started_at)
            return response
        finally:
            reset_request_id(token)

    @staticmethod
    def _log_completion(
        request: HttpRequest,
        status_code: int,
        started_at: float,
        *,
        safe_exception: dict | None = None,
    ) -> None:
        user = getattr(request, "user", None)
        user_id = getattr(user, "pk", None) if getattr(user, "is_authenticated", False) else None
        fields = {
            "event": "request_completed",
            "http_method": request.method,
            "path": request.path,
            "status_code": status_code,
            "duration_ms": round((perf_counter() - started_at) * 1000, 3),
            "user_id": user_id,
        }
        if safe_exception:
            fields["safe_exception"] = safe_exception
        level = logging.ERROR if status_code >= 500 else logging.INFO
        logger.log(level, "request completed", extra=fields)
