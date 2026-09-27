"""Server-only adapter for Numarator's versioned private API."""

import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

from django.conf import settings
from rest_framework.exceptions import APIException


class NumberingUnavailable(APIException):
    status_code = 502
    default_detail = "Numaratör işlemi tamamlanamadı. Bağlantıyı ve format yetkisini kontrol edin."


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request(path, *, payload=None, key=None):
    if not settings.NUMARATOR_BASE_URL or not settings.NUMARATOR_API_KEY:
        raise NumberingUnavailable("Numaratör bağlantısı yönetici tarafından yapılandırılmalıdır.")
    headers = {"X-API-Key": settings.NUMARATOR_API_KEY, "Accept": "application/json"}
    body = None
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if key:
        headers["Idempotency-Key"] = key
    req = Request(  # noqa: S310 -- URL is operator-configured and validated in settings.
        settings.NUMARATOR_BASE_URL.rstrip("/") + "/api/private/v1/" + path,
        data=body,
        headers=headers,
    )
    try:
        with build_opener(NoRedirect).open(req, timeout=settings.NUMARATOR_TIMEOUT) as response:
            raw = response.read(1_048_577)
        if len(raw) > 1_048_576:
            raise ValueError("Oversized provider response")
        result = json.loads(raw)
        if (
            not isinstance(result, dict)
            or result.get("success") is not True
            or "data" not in result
        ):
            raise ValueError("Invalid provider envelope")
        return result
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
        # Provider bodies and transport errors can contain credentials or private URLs.
        raise NumberingUnavailable() from exc


def validate_format(value):
    if not isinstance(value, dict) or not isinstance(value.get("code"), str):
        raise NumberingUnavailable()
    context = value.get("required_context", [])
    if not isinstance(context, list) or len(context) > 100:
        raise NumberingUnavailable()
    keys = set()
    for item in context:
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("key"), str)
            or not item["key"]
            or item["key"] in keys
            or not isinstance(item.get("max_length"), int)
            or not 1 <= item["max_length"] <= 20_000
            or not isinstance(item.get("required"), bool)
        ):
            raise NumberingUnavailable("Numaratör formatının context tanımı desteklenmiyor.")
        keys.add(item["key"])
    return value


def get_format(code):
    return validate_format(request(f"formats/{quote(code, safe='')}/")["data"])


def list_formats(page=1):
    result = request("formats/?" + urlencode({"page": page, "page_size": 100}))
    if not isinstance(result["data"], list):
        raise NumberingUnavailable()
    for item in result["data"]:
        validate_format(item)
    pagination = result.get("pagination", {})
    return {
        "results": result["data"],
        "page": page,
        "total_pages": pagination.get("total_pages", 1),
    }


def generate_number(payload, key):
    value = request("numbers/", payload=payload, key=key)["data"]
    if (
        not isinstance(value, dict)
        or not isinstance(value.get("id"), int)
        or not isinstance(value.get("document_number"), str)
        or not value["document_number"].strip()
        or len(value["document_number"]) > 20_000
    ):
        raise NumberingUnavailable()
    return {"id": value["id"], "document_number": value["document_number"]}


def preview_number(code, context):
    value = request(f"formats/{quote(code, safe='')}/preview/", payload={"context_data": context})[
        "data"
    ]
    if not isinstance(value, dict) or not isinstance(value.get("preview"), str):
        raise NumberingUnavailable()
    return value["preview"]
