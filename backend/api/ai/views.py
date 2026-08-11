import json
import logging

from django.conf import settings
from django.http import StreamingHttpResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..common.permissions import IsActiveAdminUser, IsActiveAuthenticated
from ..common.redaction import safe_exception_message
from ..services.ai_wrapper import AIProviderError
from ..services.ollama_service import OllamaService
from .serializers import OllamaChatRequestSerializer

logger = logging.getLogger(__name__)
OLLAMA_UNAVAILABLE_MESSAGE = "Ollama servisine ulaşılamadı."


def _log_ollama_error(event, exc):
    logger.error(
        "Ollama operation failed: %s",
        safe_exception_message(exc),
        extra={"event": event},
    )


class OllamaStatusView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def get(self, request):
        payload = dict(OllamaService().status())
        if not request.user.is_staff:
            payload.pop("base_url", None)
        if payload.get("error"):
            payload["error"] = OLLAMA_UNAVAILABLE_MESSAGE
        return Response(payload)


class OllamaPullView(APIView):
    permission_classes = [IsActiveAdminUser]

    def post(self, request):
        try:
            result = OllamaService().pull()
        except AIProviderError as exc:
            _log_ollama_error("ollama_pull_failed", exc)
            return Response(
                {"detail": OLLAMA_UNAVAILABLE_MESSAGE},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response({"model": settings.OLLAMA_MODEL, **result})


class OllamaUnloadView(APIView):
    permission_classes = [IsActiveAdminUser]

    def post(self, request):
        try:
            OllamaService().unload()
        except AIProviderError as exc:
            _log_ollama_error("ollama_unload_failed", exc)
            return Response(
                {"detail": OLLAMA_UNAVAILABLE_MESSAGE},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response({"status": "unloaded", "model": settings.OLLAMA_MODEL})


class OllamaChatView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def post(self, request):
        serializer = OllamaChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.to_ollama_payload()
        service = OllamaService(model=payload["model"])

        def stream():
            try:
                for chunk in service.chat_stream(payload):
                    yield json.dumps(chunk, ensure_ascii=False) + "\n"
            except AIProviderError as exc:
                _log_ollama_error("ollama_chat_failed", exc)
                yield (
                    json.dumps(
                        {"error": OLLAMA_UNAVAILABLE_MESSAGE},
                        ensure_ascii=False,
                    )
                    + "\n"
                )

        response = StreamingHttpResponse(stream(), content_type="application/x-ndjson")
        response["Cache-Control"] = "no-cache, no-transform"
        response["X-Accel-Buffering"] = "no"
        return response
