import json
import logging
from pathlib import Path

from django.contrib.auth import get_user_model, login, logout
from django.conf import settings
from django.core.mail import EmailMessage
from django.http import FileResponse, StreamingHttpResponse
from django.db.models import Prefetch, Q
from django.middleware.csrf import get_token
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import SAFE_METHODS, AllowAny, BasePermission, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    AnalysisControl,
    AsyncJob,
    Document,
    DocumentAnalysisRun,
    FlightPermit,
    PanelResponsible,
    Person,
    PersonGroup,
    Project,
    ProjectPanel,
    TechnicalDocument,
    TechnicalDocumentNotification,
)
from .serializers import (
    AdminUserSerializer,
    AdminUserStatusSerializer,
    AnalysisControlSerializer,
    AsyncJobSerializer,
    DocumentAnalysisRunSerializer,
    DocumentControlRunSerializer,
    DocumentDetailSerializer,
    DocumentListSerializer,
    DocumentUploadSerializer,
    DocumentRagQuerySerializer,
    FlightPermitSerializer,
    LoginSerializer,
    OllamaChatRequestSerializer,
    PanelResponsibleSerializer,
    PersonGroupSerializer,
    PersonSerializer,
    ProjectPanelSerializer,
    ProjectSerializer,
    RegisterSerializer,
    TechnicalDocumentNotificationRequestSerializer,
    TechnicalDocumentSerializer,
    UserSerializer,
)
# Kept as a public import for backwards-compatible integrations and test patches.
from .services.ai_processor import process_document_text  # noqa: F401
from .services.word_table_parser import WordTableParseError, parse_word_table
from .services.word_to_jira import build_jira_draft, publish_jira_draft
from .services.jira_connector import JiraConnectorError
from .services.ai_wrapper import AIProviderError
from .services.ollama_service import OllamaService
from .services.rag_service import (
    SYSTEM_CONTROLS,
    answer_document_query,
    run_document_controls,
)
from .services.job_queue import enqueue_document_processing
from .services.flight_permit_document import build_flight_permit_document

User = get_user_model()
logger = logging.getLogger(__name__)


class IsActiveAuthenticated(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_active


class IsActiveAdminUser(IsAdminUser):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_active


class IsOrganizationReaderOrAdmin(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated or not request.user.is_active:
            return False
        return request.method in SAFE_METHODS or request.user.is_staff


@api_view(["GET"])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def health_check(_request):
    return Response(
        {
            "status": "ok",
            "service": "uav-center-backend",
            "timestamp": timezone.now().isoformat(),
        }
    )


class CsrfTokenView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        return Response({"csrfToken": get_token(request)})


class CurrentUserView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        if not request.user.is_authenticated or not request.user.is_active:
            if request.user.is_authenticated:
                logout(request)
            return Response({"authenticated": False, "user": None})

        return Response(
            {
                "authenticated": True,
                "user": UserSerializer(request.user).data,
            }
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        login(request, serializer.validated_data["user"])
        return Response(
            {
                "authenticated": True,
                "user": UserSerializer(request.user).data,
            }
        )


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "authenticated": False,
                "user": UserSerializer(user).data,
                "message": "Üyelik isteğiniz alındı. Admin onayından sonra giriş yapabilirsiniz.",
            },
            status=status.HTTP_201_CREATED,
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminUserListView(generics.ListAPIView):
    permission_classes = [IsActiveAdminUser]
    serializer_class = AdminUserSerializer

    def get_queryset(self):
        return User.objects.order_by("is_active", "-date_joined")


class AdminUserStatusView(APIView):
    permission_classes = [IsActiveAdminUser]

    def patch(self, request, user_id):
        user = generics.get_object_or_404(User, pk=user_id)
        serializer = AdminUserStatusSerializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(AdminUserSerializer(user).data)


class DocumentListView(generics.ListAPIView):
    permission_classes = [IsActiveAuthenticated]
    serializer_class = DocumentListSerializer

    def get_queryset(self):
        return Document.objects.all()[:50]


class DocumentDetailView(generics.RetrieveDestroyAPIView):
    permission_classes = [IsActiveAuthenticated]
    queryset = Document.objects.all()
    serializer_class = DocumentDetailSerializer
    lookup_url_kwarg = "document_id"

    def perform_destroy(self, instance):
        instance.file.delete(save=False)
        instance.delete()


class DocumentUploadView(APIView):
    permission_classes = [IsActiveAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = DocumentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        upload = serializer.validated_data["file"]
        prompt = serializer.validated_data["prompt"]
        use_ocr = serializer.validated_data["use_ocr"]
        use_ai = serializer.validated_data["use_ai"]
        document = Document.objects.create(
            original_name=upload.name,
            file=upload,
            content_type=upload.content_type or "",
            size=upload.size,
            prompt=prompt,
        )
        job = enqueue_document_processing(
            document=document,
            owner=request.user,
            use_ocr=use_ocr,
            use_ai=use_ai,
        )
        return Response(
            {
                "job": AsyncJobSerializer(job).data,
                "document": DocumentDetailSerializer(document).data,
            },
            status=status.HTTP_202_ACCEPTED,
        )


class AsyncJobListView(generics.ListAPIView):
    permission_classes = [IsActiveAuthenticated]
    serializer_class = AsyncJobSerializer

    def get_queryset(self):
        queryset = AsyncJob.objects.filter(owner=self.request.user).select_related("document")
        status_value = self.request.query_params.get("status", "").strip()
        if status_value in dict(AsyncJob.STATUS_CHOICES):
            queryset = queryset.filter(status=status_value)
        try:
            limit = min(max(int(self.request.query_params.get("limit", 100)), 1), 200)
        except (TypeError, ValueError):
            limit = 100
        return queryset[:limit]


class AsyncJobDetailView(generics.RetrieveAPIView):
    permission_classes = [IsActiveAuthenticated]
    serializer_class = AsyncJobSerializer
    lookup_url_kwarg = "job_id"

    def get_queryset(self):
        return AsyncJob.objects.filter(owner=self.request.user).select_related("document")


class AsyncJobCancelView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def post(self, request, job_id):
        job = generics.get_object_or_404(AsyncJob, pk=job_id, owner=request.user)
        if job.status != AsyncJob.STATUS_QUEUED:
            return Response(
                {"detail": "Yalnızca sırada bekleyen joblar iptal edilebilir."},
                status=status.HTTP_409_CONFLICT,
            )
        now = timezone.now()
        updated = AsyncJob.objects.filter(
            pk=job.pk,
            owner=request.user,
            status=AsyncJob.STATUS_QUEUED,
        ).update(
            status=AsyncJob.STATUS_CANCELLED,
            completed_at=now,
            locked_at=None,
            locked_by="",
        )
        if not updated:
            return Response(
                {"detail": "Job worker tarafından alınmış; artık iptal edilemez."},
                status=status.HTTP_409_CONFLICT,
            )
        job.refresh_from_db()
        return Response(AsyncJobSerializer(job).data)


class AnalysisControlListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsActiveAuthenticated]
    serializer_class = AnalysisControlSerializer

    def get_queryset(self):
        return AnalysisControl.objects.filter(owner=self.request.user)

    def list(self, request, *args, **kwargs):
        system_controls = [
            {**control, "is_active": True, "instructions": ""}
            for control in SYSTEM_CONTROLS.values()
        ]
        custom_controls = self.get_serializer(self.get_queryset(), many=True).data
        return Response(system_controls + custom_controls)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class AnalysisControlDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsActiveAuthenticated]
    serializer_class = AnalysisControlSerializer
    lookup_url_kwarg = "control_id"

    def get_queryset(self):
        return AnalysisControl.objects.filter(owner=self.request.user)


class DocumentRagQueryView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def post(self, request, document_id):
        document = generics.get_object_or_404(Document, pk=document_id)
        serializer = DocumentRagQuerySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        query = serializer.validated_data["query"]
        run = DocumentAnalysisRun.objects.create(
            document=document,
            created_by=request.user,
            query=query,
            status=DocumentAnalysisRun.STATUS_PENDING,
        )
        try:
            result = answer_document_query(
                document,
                query,
                top_k=serializer.validated_data["top_k"],
            )
        except Exception as exc:
            logger.exception("RAG query failed for document %s", document.pk)
            run.status = DocumentAnalysisRun.STATUS_FAILED
            run.error_message = str(exc)[:4000]
            run.completed_at = timezone.now()
            run.save(update_fields=["status", "error_message", "completed_at"])
            return Response(
                {"detail": "Doküman sorgusu tamamlanamadı.", "run_id": run.pk},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        run.result = result
        run.status = DocumentAnalysisRun.STATUS_COMPLETED
        run.completed_at = timezone.now()
        run.save(update_fields=["result", "status", "completed_at"])
        return Response(DocumentAnalysisRunSerializer(run).data)


class DocumentControlRunView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def post(self, request, document_id):
        document = generics.get_object_or_404(Document, pk=document_id)
        serializer = DocumentControlRunSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        control_ids = serializer.validated_data["control_ids"]
        run = DocumentAnalysisRun.objects.create(
            document=document,
            created_by=request.user,
            status=DocumentAnalysisRun.STATUS_PENDING,
            controls=control_ids,
        )
        try:
            results = run_document_controls(document, request.user, control_ids)
        except ValueError as exc:
            run.status = DocumentAnalysisRun.STATUS_FAILED
            run.error_message = str(exc)[:4000]
            run.completed_at = timezone.now()
            run.save(update_fields=["status", "error_message", "completed_at"])
            return Response({"detail": str(exc), "run_id": run.pk}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.exception("Document controls failed for document %s", document.pk)
            run.status = DocumentAnalysisRun.STATUS_FAILED
            run.error_message = str(exc)[:4000]
            run.completed_at = timezone.now()
            run.save(update_fields=["status", "error_message", "completed_at"])
            return Response(
                {"detail": "Doküman kontrolleri tamamlanamadı.", "run_id": run.pk},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        run.status = DocumentAnalysisRun.STATUS_COMPLETED
        run.result = {"controls": results}
        run.completed_at = timezone.now()
        run.save(update_fields=["status", "result", "completed_at"])
        return Response(DocumentAnalysisRunSerializer(run).data)


class DocumentAnalysisRunListView(generics.ListAPIView):
    permission_classes = [IsActiveAuthenticated]
    serializer_class = DocumentAnalysisRunSerializer

    def get_queryset(self):
        document = generics.get_object_or_404(Document, pk=self.kwargs["document_id"])
        return document.analysis_runs.filter(created_by=self.request.user)[:25]


class OllamaStatusView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def get(self, request):
        return Response(OllamaService().status())


class OllamaPullView(APIView):
    permission_classes = [IsActiveAdminUser]

    def post(self, request):
        try:
            result = OllamaService().pull()
        except AIProviderError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        return Response({"model": settings.OLLAMA_MODEL, **result})


class OllamaUnloadView(APIView):
    permission_classes = [IsActiveAdminUser]

    def post(self, request):
        try:
            OllamaService().unload()
        except AIProviderError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
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
                yield json.dumps({"error": str(exc)}, ensure_ascii=False) + "\n"

        response = StreamingHttpResponse(stream(), content_type="application/x-ndjson")
        response["Cache-Control"] = "no-cache, no-transform"
        response["X-Accel-Buffering"] = "no"
        return response


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

        from tempfile import NamedTemporaryFile

        try:
            with NamedTemporaryFile(suffix=".docx") as temporary_file:
                for chunk in upload.chunks():
                    temporary_file.write(chunk)
                temporary_file.flush()
                result = parse_word_table(temporary_file.name)
        except WordTableParseError as exc:
            return Response(
                {"detail": str(exc)},
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
    permission_classes = [IsActiveAuthenticated]

    def post(self, request):
        task = request.data.get("task")
        subtasks = request.data.get("subtasks", [])
        if not isinstance(task, dict):
            return Response(
                {"task": ["Ana Task bilgileri zorunludur."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not str(task.get("project_key") or "").strip():
            return Response(
                {"project_key": ["Jira proje anahtarı zorunludur."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not str(task.get("summary") or "").strip():
            return Response(
                {"summary": ["Task özeti zorunludur."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not isinstance(subtasks, list):
            return Response(
                {"subtasks": ["Alt görevler liste biçiminde olmalıdır."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        enabled_subtasks = [item for item in subtasks if item.get("enabled", True)]
        if any(not str(item.get("summary") or "").strip() for item in enabled_subtasks):
            return Response(
                {"subtasks": ["Dahil edilen her alt görev için özet zorunludur."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            result = publish_jira_draft({"task": task, "subtasks": subtasks})
        except JiraConnectorError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response(
            result,
            status=(
                status.HTTP_201_CREATED
                if result["status"] == "created"
                else status.HTTP_200_OK
            ),
        )


class ProjectListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsOrganizationReaderOrAdmin]
    serializer_class = ProjectSerializer

    def get_queryset(self):
        return Project.objects.prefetch_related("panels__responsibles").all()


class ProjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsOrganizationReaderOrAdmin]
    serializer_class = ProjectSerializer
    queryset = Project.objects.prefetch_related("panels__responsibles")
    lookup_url_kwarg = "project_id"


class ProjectPanelListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsOrganizationReaderOrAdmin]
    serializer_class = ProjectPanelSerializer

    def get_queryset(self):
        return ProjectPanel.objects.filter(project_id=self.kwargs["project_id"]).prefetch_related(
            "responsibles"
        )

    def perform_create(self, serializer):
        project = generics.get_object_or_404(Project, pk=self.kwargs["project_id"])
        serializer.save(project=project)


class ProjectPanelDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsOrganizationReaderOrAdmin]
    serializer_class = ProjectPanelSerializer
    queryset = ProjectPanel.objects.prefetch_related("responsibles")
    lookup_url_kwarg = "panel_id"


class PanelResponsibleListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsOrganizationReaderOrAdmin]
    serializer_class = PanelResponsibleSerializer

    def get_queryset(self):
        return PanelResponsible.objects.filter(panel_id=self.kwargs["panel_id"])

    def perform_create(self, serializer):
        panel = generics.get_object_or_404(ProjectPanel, pk=self.kwargs["panel_id"])
        serializer.save(panel=panel)


class PanelResponsibleDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsOrganizationReaderOrAdmin]
    serializer_class = PanelResponsibleSerializer
    queryset = PanelResponsible.objects.all()
    lookup_url_kwarg = "responsible_id"


class PersonGroupListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsOrganizationReaderOrAdmin]
    serializer_class = PersonGroupSerializer

    def get_queryset(self):
        return PersonGroup.objects.prefetch_related("people__groups").all()


class PersonGroupDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsOrganizationReaderOrAdmin]
    serializer_class = PersonGroupSerializer
    queryset = PersonGroup.objects.prefetch_related("people__groups")
    lookup_url_kwarg = "group_id"


class GroupPersonListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsOrganizationReaderOrAdmin]
    serializer_class = PersonSerializer

    def get_queryset(self):
        return Person.objects.filter(groups__id=self.kwargs["group_id"]).prefetch_related("groups")

    def perform_create(self, serializer):
        group = generics.get_object_or_404(PersonGroup, pk=self.kwargs["group_id"])
        person = serializer.save()
        group.people.add(person)


class PersonDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsOrganizationReaderOrAdmin]
    serializer_class = PersonSerializer
    queryset = Person.objects.prefetch_related("groups")
    lookup_url_kwarg = "person_id"


class FlightPermitListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsActiveAuthenticated]
    serializer_class = FlightPermitSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        queryset = FlightPermit.objects.select_related("created_by", "updated_by")
        search = self.request.query_params.get("search", "").strip()
        status_value = self.request.query_params.get("status", "").strip()
        permit_type = self.request.query_params.get("permit_type", "").strip()
        if search:
            queryset = queryset.filter(
                Q(aircraft_number__icontains=search)
                | Q(permit_number__icontains=search)
                | Q(issuing_authority__icontains=search)
                | Q(flight_region__icontains=search)
            )
        if status_value:
            queryset = queryset.filter(status=status_value)
        if permit_type:
            queryset = queryset.filter(permit_type=permit_type)
        return queryset


class FlightPermitDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsActiveAuthenticated]
    serializer_class = FlightPermitSerializer
    parser_classes = [MultiPartParser, FormParser]
    queryset = FlightPermit.objects.select_related("created_by", "updated_by")
    lookup_url_kwarg = "flight_permit_id"

    def perform_destroy(self, instance):
        if instance.document:
            instance.document.delete(save=False)
        instance.delete()


class FlightPermitDocumentView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def get(self, request, flight_permit_id):
        permit = generics.get_object_or_404(FlightPermit, pk=flight_permit_id)
        if not permit.document:
            return Response({"detail": "Bu uçuş iznine doküman eklenmemiş."}, status=404)
        response = FileResponse(
            permit.document.open("rb"),
            as_attachment=False,
            filename=permit.document_name or Path(permit.document.name).name,
            content_type=permit.document_content_type or "application/octet-stream",
        )
        response["X-Content-Type-Options"] = "nosniff"
        return response


class FlightPermitGeneratedDocumentView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def get(self, request, flight_permit_id):
        permit = generics.get_object_or_404(FlightPermit, pk=flight_permit_id)
        document = build_flight_permit_document(permit)
        safe_aircraft_number = "".join(
            character if character.isalnum() or character in {"-", "_"} else "_"
            for character in permit.aircraft_number
        )
        safe_permit_number = "".join(
            character if character.isalnum() or character in {"-", "_"} else "_"
            for character in permit.permit_number
        )
        response = FileResponse(
            document,
            as_attachment=True,
            filename=f"Ucus_Izni_{safe_aircraft_number}_{safe_permit_number}.docx",
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        response["X-Content-Type-Options"] = "nosniff"
        return response


def technical_document_queryset():
    return TechnicalDocument.objects.select_related(
        "project",
        "cover_page",
        "created_by",
        "updated_by",
    ).prefetch_related(
        Prefetch(
            "panels",
            queryset=ProjectPanel.objects.prefetch_related("responsibles"),
        ),
        "status_history__changed_by",
        "notifications__sent_by",
    )


class TechnicalDocumentListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsOrganizationReaderOrAdmin]
    serializer_class = TechnicalDocumentSerializer

    def get_queryset(self):
        queryset = technical_document_queryset()
        project_id = self.request.query_params.get("project")
        panel_id = self.request.query_params.get("panel")
        status_value = self.request.query_params.get("status")
        search = self.request.query_params.get("search", "").strip()

        if project_id:
            queryset = queryset.filter(project_id=project_id)
        if panel_id:
            queryset = queryset.filter(panels__id=panel_id)
        if status_value:
            queryset = queryset.filter(status=status_value)
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search)
                | Q(title__icontains=search)
                | Q(category__icontains=search)
                | Q(owner_name__icontains=search)
                | Q(cover_page__number__icontains=search)
                | Q(cover_page__issue__icontains=search)
            )
        return queryset.distinct()


class TechnicalDocumentDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsOrganizationReaderOrAdmin]
    serializer_class = TechnicalDocumentSerializer
    queryset = technical_document_queryset()
    lookup_url_kwarg = "technical_document_id"


class TechnicalDocumentNotifyView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def post(self, request, technical_document_id):
        document = generics.get_object_or_404(
            technical_document_queryset(),
            pk=technical_document_id,
        )
        serializer = TechnicalDocumentNotificationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        recipients = sorted(
            {
                responsible.email.strip().lower()
                for panel in document.panels.all()
                for responsible in panel.responsibles.all()
                if responsible.email.strip()
            }
        )
        if not recipients:
            return Response(
                {"detail": "Seçili panellerde e-posta adresi bulunan sorumlu yok."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        subject = serializer.validated_data.get("subject", "").strip() or (
            f"[{document.project.code}] {document.code} — {document.title}"
        )
        custom_message = serializer.validated_data.get("message", "").strip()
        message = custom_message or (
            f"{document.code} kodlu “{document.title}” dokümanı için bilgilendirme.\n\n"
            f"Durum: {document.get_status_display()}\n"
            f"Revizyon: {document.revision}\n"
            f"Yayın tarihi: {document.publication_date or '—'}\n"
            f"Termin: {document.due_date or '—'}\n\n"
            "Bu ileti UAV Center Teknik Doküman Yönetimi üzerinden gönderilmiştir."
        )

        notification = TechnicalDocumentNotification(
            document=document,
            subject=subject,
            message=message,
            recipients=recipients,
            recipient_count=len(recipients),
            status=TechnicalDocumentNotification.STATUS_SENT,
            sent_by=request.user,
        )

        try:
            email = EmailMessage(
                subject=subject,
                body=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                bcc=recipients,
            )
            email.send(fail_silently=False)
        except Exception as exc:
            notification.status = TechnicalDocumentNotification.STATUS_FAILED
            notification.error_message = str(exc)
            notification.save()
            return Response(
                {
                    "detail": "E-posta gönderilemedi. Hata denetim kaydına işlendi.",
                    "notification": {
                        "id": notification.id,
                        "status": notification.status,
                    },
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        notification.save()
        document.last_notification_at = notification.created_at
        document.last_notification_recipient_count = len(recipients)
        document.save(
            update_fields=[
                "last_notification_at",
                "last_notification_recipient_count",
            ]
        )
        return Response(
            {
                "message": f"Bildirim {len(recipients)} panel sorumlusuna gönderildi.",
                "document": TechnicalDocumentSerializer(
                    technical_document_queryset().get(pk=document.pk),
                    context={"request": request},
                ).data,
            }
        )
