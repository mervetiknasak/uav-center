from django.utils import timezone
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Document
from .serializers import DocumentDetailSerializer, DocumentListSerializer, DocumentUploadSerializer
from .services.ai_processor import process_document_text
from .services.document_extractor import UnsupportedDocumentError, extract_text


@api_view(["GET"])
def health_check(_request):
    return Response(
        {
            "status": "ok",
            "service": "uav-center-backend",
            "timestamp": timezone.now().isoformat(),
        }
    )


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
