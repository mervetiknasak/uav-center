import logging

from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from ..common.permissions import IsActiveAdminUser, IsActiveAuthenticated
from ..common.redaction import safe_exception_message
from ..services.document_limits import (
    DocumentPreflightError,
    preflight_document,
    validate_upload_size,
)
from ..services.jira_connector import JiraConnector, JiraConnectorError
from ..services.word_table_parser import WordTableParseError, parse_word_table
from ..services.word_to_jira import build_jira_draft, publish_jira_draft
from .serializers import WordToJiraPublishRequestSerializer

logger = logging.getLogger(__name__)


class WordTableParseView(APIView):
    permission_classes = [IsActiveAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        upload = request.FILES.get("file")
        if upload is None:
            return Response(
                {"file": ["Word dosyası zorunludur."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not upload.name.lower().endswith(".docx"):
            return Response(
                {"file": ["Yalnızca .docx uzantılı Word dosyaları destekleniyor."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validate_upload_size(upload.size)
            preflight_document(upload, ".docx")
        except DocumentPreflightError as exc:
            return Response(
                {"file": [str(exc)]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from tempfile import NamedTemporaryFile

        try:
            with NamedTemporaryFile(suffix=".docx") as temporary_file:
                for chunk in upload.chunks():
                    temporary_file.write(chunk)
                temporary_file.flush()
                result = parse_word_table(temporary_file.name)
        except WordTableParseError as exc:
            logger.warning(
                "Word table parsing failed: %s",
                safe_exception_message(exc),
                extra={"event": "word_table_parse_failed"},
            )
            return Response(
                {"detail": "Word dosyası işlenemedi."},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        return Response(
            {
                "file_name": upload.name,
                **result,
                "jira_draft": build_jira_draft(result["extracted_data"]),
                "jira_ready": bool(result["extracted_data"]["action_items"]),
            }
        )


class WordToJiraPublishView(APIView):
    permission_classes = [IsActiveAdminUser]

    def post(self, request):
        serializer = WordToJiraPublishRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            result = publish_jira_draft(
                serializer.validated_data,
                jira=JiraConnector(),
            )
        except JiraConnectorError as exc:
            logger.error(
                "Jira meeting publish failed: %s",
                safe_exception_message(exc),
                extra={"event": "jira_meeting_publish_failed"},
            )
            return Response(
                {"detail": "Jira aktarımı tamamlanamadı."},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response(
            result,
            status=(
                status.HTTP_201_CREATED if result["status"] == "created" else status.HTTP_200_OK
            ),
        )
