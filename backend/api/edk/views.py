import logging

from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404
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
from .jira import build_jira_draft, publish_jira_draft
from .minutes_parser import EDKMinutesParseError, parse_minutes_document
from .models import EDKApplication
from .roles import (
    EDK_ROLE_APPLICANT,
    EDK_ROLE_APPROVER,
    user_has_edk_role,
)
from .selectors import edk_applications_visible_to
from .serializers import (
    EDKApplicationDecisionSerializer,
    EDKApplicationSerializer,
    EDKJiraPublishRequestSerializer,
)
from .services import (
    EDKApplicationConflict,
    decide_edk_application,
    record_minutes_upload,
)

logger = logging.getLogger(__name__)


def _parse_minutes_upload(request, application):
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
            result = parse_minutes_document(temporary_file.name)
    except EDKMinutesParseError as exc:
        logger.warning(
            "Word table parsing failed: %s",
            safe_exception_message(exc),
            extra={"event": "word_table_parse_failed"},
        )
        return Response(
            {"detail": "Word dosyası işlenemedi."},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    record_minutes_upload(application=application, file_name=upload.name)
    return Response(
        {
            "application_id": application.id,
            "file_name": upload.name,
            **result,
            "jira_draft": build_jira_draft(result["extracted_data"]),
            "jira_ready": bool(result["extracted_data"]["action_items"]),
        }
    )


class EDKApplicationListCreateView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def get(self, request):
        if not any(
            user_has_edk_role(request.user, role)
            for role in (EDK_ROLE_APPLICANT, EDK_ROLE_APPROVER)
        ):
            raise PermissionDenied("EDK rolünüz bulunmuyor.")
        serializer = EDKApplicationSerializer(
            edk_applications_visible_to(request.user)[:200],
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)

    def post(self, request):
        if not user_has_edk_role(request.user, EDK_ROLE_APPLICANT):
            raise PermissionDenied("EDK başvurusu oluşturma rolünüz bulunmuyor.")
        serializer = EDKApplicationSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        application = serializer.save()
        return Response(
            EDKApplicationSerializer(
                application,
                context={"request": request},
            ).data,
            status=status.HTTP_201_CREATED,
        )


class EDKApplicationDetailView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def get(self, request, application_id):
        if not any(
            user_has_edk_role(request.user, role)
            for role in (EDK_ROLE_APPLICANT, EDK_ROLE_APPROVER)
        ):
            raise PermissionDenied("EDK rolünüz bulunmuyor.")
        application = get_object_or_404(
            edk_applications_visible_to(request.user),
            pk=application_id,
        )
        return Response(
            EDKApplicationSerializer(
                application,
                context={"request": request},
            ).data
        )


class EDKApplicationDecisionView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def post(self, request, application_id):
        if not user_has_edk_role(request.user, EDK_ROLE_APPROVER):
            raise PermissionDenied("EDK başvurusu onaylama rolünüz bulunmuyor.")
        application = get_object_or_404(EDKApplication, pk=application_id)
        serializer = EDKApplicationDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            application = decide_edk_application(
                application=application,
                reviewer=request.user,
                **serializer.validated_data,
            )
        except EDKApplicationConflict as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(
            EDKApplicationSerializer(
                application,
                context={"request": request},
            ).data
        )


class EDKMeetingMinutesParseView(APIView):
    permission_classes = [IsActiveAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, application_id):
        if not user_has_edk_role(request.user, EDK_ROLE_APPLICANT):
            raise PermissionDenied("Toplantı tutanağı yükleme rolünüz bulunmuyor.")
        application = get_object_or_404(
            EDKApplication,
            pk=application_id,
            applicant=request.user,
        )
        if application.status != EDKApplication.STATUS_APPROVED:
            return Response(
                {"detail": "Toplantı tutanağı yalnızca onaylanan başvurulara yüklenebilir."},
                status=status.HTTP_409_CONFLICT,
            )
        return _parse_minutes_upload(request, application)


class EDKJiraPublishView(APIView):
    permission_classes = [IsActiveAdminUser]

    def post(self, request):
        serializer = EDKJiraPublishRequestSerializer(data=request.data)
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
