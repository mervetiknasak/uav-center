import logging

from django.db import DatabaseError, connection
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .redaction import safe_exception_message

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([AllowAny])
def readiness_check(_request):
    """Report whether this process can serve requests that require the database."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except DatabaseError as exc:
        logger.error(
            "Database readiness check failed: %s",
            safe_exception_message(exc),
            extra={"event": "readiness_failed"},
        )
        return Response(
            {"status": "unavailable", "database": "unavailable"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    return Response({"status": "ready", "database": "ok"})
