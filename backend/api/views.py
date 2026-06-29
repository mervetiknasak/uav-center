from django.contrib.auth import get_user_model, login, logout
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

from .models import Document, PanelResponsible, Project, ProjectPanel
from .serializers import (
    AdminUserSerializer,
    AdminUserStatusSerializer,
    DocumentDetailSerializer,
    DocumentListSerializer,
    DocumentUploadSerializer,
    LoginSerializer,
    PanelResponsibleSerializer,
    ProjectPanelSerializer,
    ProjectSerializer,
    RegisterSerializer,
    UserSerializer,
)
from .services.ai_processor import process_document_text
from .services.document_extractor import UnsupportedDocumentError, extract_text

User = get_user_model()


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
        document = Document.objects.create(
            original_name=upload.name,
            file=upload,
            content_type=upload.content_type or "",
            size=upload.size,
            prompt=prompt,
        )

        try:
            extracted_text = extract_text(document.file.path)
            ai_result = process_document_text(extracted_text, document.original_name, prompt)
            document.extracted_text = extracted_text
            document.ai_result = ai_result
            document.status = Document.STATUS_PROCESSED
            document.processed_at = timezone.now()
            document.error_message = ""
        except UnsupportedDocumentError as exc:
            document.status = Document.STATUS_FAILED
            document.error_message = str(exc)
            document.processed_at = timezone.now()
        except Exception as exc:
            document.status = Document.STATUS_FAILED
            document.error_message = f"Dosya işlenemedi: {exc}"
            document.processed_at = timezone.now()

        document.save(
            update_fields=[
                "extracted_text",
                "ai_result",
                "status",
                "processed_at",
                "error_message",
            ]
        )

        response_status = (
            status.HTTP_201_CREATED
            if document.status == Document.STATUS_PROCESSED
            else status.HTTP_422_UNPROCESSABLE_ENTITY
        )
        return Response(DocumentDetailSerializer(document).data, status=response_status)


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
