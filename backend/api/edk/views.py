import logging
from pathlib import Path
from tempfile import TemporaryDirectory

from django.http import FileResponse
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
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
from .file_policy import presentation_content_type
from .jira import build_jira_draft, fetch_jira_tracking, publish_jira_draft
from .minutes_parser import EDKMinutesParseError, parse_minutes_document
from .models import EDKApplication
from .roles import (
    EDK_ROLE_APPLICANT,
    EDK_ROLE_APPROVER,
    user_has_edk_role,
)
from .selectors import (
    edk_applications_publishable_to_jira_by,
    edk_applications_visible_to,
)
from .serializers import (
    EDKApplicationDecisionSerializer,
    EDKApplicationSerializer,
    EDKJiraPublishRequestSerializer,
)
from .services import (
    EDKApplicationConflict,
    EDKJiraConflict,
    decide_edk_application,
    jira_tracking_payload,
    link_edk_jira_issue,
    record_edk_jira_tracking,
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

    try:
        with TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory) / "minutes.docx"
            with temporary_path.open("wb") as temporary_file:
                for chunk in upload.chunks():
                    temporary_file.write(chunk)

            result = parse_minutes_document(temporary_path)
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
    parser_classes = [JSONParser, MultiPartParser, FormParser]

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


class EDKApplicationPresentationView(APIView):
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
        if not application.presentation:
            return Response(
                {"detail": "Bu başvuruya sunum eklenmemiş."},
                status=status.HTTP_404_NOT_FOUND,
            )
        filename = application.presentation_file_name or Path(application.presentation.name).name
        response = FileResponse(
            application.presentation.open("rb"),
            as_attachment=True,
            filename=filename,
            content_type=(
                application.presentation_content_type or presentation_content_type(filename)
            ),
        )
        response["X-Content-Type-Options"] = "nosniff"
        return response


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
        payload = dict(serializer.validated_data)
        jsession = payload.pop("jsession")
        try:
            result = publish_jira_draft(
                payload,
                jira=JiraConnector(jsession=jsession),
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


class EDKApplicationJiraPublishView(APIView):
    """Publish a draft and durably bind the resulting parent Task to one EDK."""

    permission_classes = [IsActiveAuthenticated]

    def post(self, request, application_id):
        application = get_object_or_404(
            edk_applications_publishable_to_jira_by(request.user),
            pk=application_id,
        )
        if (
            application.status != EDKApplication.STATUS_APPROVED
            or not application.minutes_file_name
        ):
            return Response(
                {"detail": "Jira aktarımı için onaylı EDK toplantı tutanağı gereklidir."},
                status=status.HTTP_409_CONFLICT,
            )
        if application.jira_issue_key:
            return Response(
                {"detail": "Bu EDK zaten bir Jira Task'ına bağlı."},
                status=status.HTTP_409_CONFLICT,
            )
        serializer = EDKJiraPublishRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = dict(serializer.validated_data)
        jsession = payload.pop("jsession")
        try:
            jira = JiraConnector(jsession=jsession)
            result = publish_jira_draft(payload, jira=jira)
            application = link_edk_jira_issue(
                application=application,
                issue_key=result["task"]["key"],
                url=result["task"]["url"],
                summary=serializer.validated_data["task"]["summary"],
            )
        except JiraConnectorError as exc:
            logger.error(
                "EDK Jira publish failed: %s",
                safe_exception_message(exc),
                extra={
                    "event": "edk_jira_publish_failed",
                    "edk_application_id": application_id,
                },
            )
            return Response(
                {"detail": "Jira aktarımı tamamlanamadı."},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except EDKJiraConflict as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_409_CONFLICT,
            )

        try:
            tracking = fetch_jira_tracking(application.jira_issue_key, jira=jira)
            application = record_edk_jira_tracking(
                application=application,
                tracking=tracking,
            )
        except JiraConnectorError as exc:
            logger.error(
                "EDK Jira initial tracking refresh failed: %s",
                safe_exception_message(exc),
                extra={
                    "event": "edk_jira_initial_refresh_failed",
                    "edk_application_id": application_id,
                },
            )
            result["message"] = " ".join(
                part
                for part in (
                    result.get("message", ""),
                    "Task EDK'ya bağlandı; Jira durumu daha sonra yenilenmelidir.",
                )
                if part
            )
        except EDKJiraConflict as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_409_CONFLICT,
            )

        result["tracking"] = jira_tracking_payload(application)
        return Response(
            result,
            status=(
                status.HTTP_201_CREATED if result["status"] == "created" else status.HTTP_200_OK
            ),
        )


class EDKApplicationJiraRefreshView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def post(self, request, application_id):
        if not any(
            user_has_edk_role(request.user, role)
            for role in (EDK_ROLE_APPLICANT, EDK_ROLE_APPROVER)
        ):
            raise PermissionDenied("EDK rolünüz bulunmuyor.")
        application = get_object_or_404(
            edk_applications_visible_to(request.user),
            pk=application_id,
        )
        if not application.jira_issue_key:
            return Response(
                {"detail": "Bu EDK henüz bir Jira Task'ına bağlı değil."},
                status=status.HTTP_409_CONFLICT,
            )
        try:
            jira = JiraConnector()
            tracking = fetch_jira_tracking(application.jira_issue_key, jira=jira)
            application = record_edk_jira_tracking(
                application=application,
                tracking=tracking,
            )
        except JiraConnectorError as exc:
            logger.error(
                "EDK Jira tracking refresh failed: %s",
                safe_exception_message(exc),
                extra={
                    "event": "edk_jira_tracking_refresh_failed",
                    "edk_application_id": application_id,
                },
            )
            return Response(
                {"detail": "Jira takip bilgisi yenilenemedi."},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except EDKJiraConflict as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(jira_tracking_payload(application))
