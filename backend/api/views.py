from django.contrib.auth import login, logout
from django.middleware.csrf import get_token
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Document
from .serializers import (
    DocumentDetailSerializer,
    DocumentListSerializer,
    DocumentUploadSerializer,
    LoginSerializer,
    RegisterSerializer,
    UserSerializer,
)
from .services.ai_processor import process_document_text
from .services.document_extractor import UnsupportedDocumentError, extract_text


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
        if not request.user.is_authenticated:
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
        login(request, user)
        return Response(
            {
                "authenticated": True,
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class DocumentListView(generics.ListAPIView):
    serializer_class = DocumentListSerializer

    def get_queryset(self):
        return Document.objects.all()[:50]


class DocumentDetailView(generics.RetrieveDestroyAPIView):
    queryset = Document.objects.all()
    serializer_class = DocumentDetailSerializer
    lookup_url_kwarg = "document_id"

    def perform_destroy(self, instance):
        instance.file.delete(save=False)
        instance.delete()


class DocumentUploadView(APIView):
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
