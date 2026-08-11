import logging

from django.utils import timezone
from rest_framework import generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from ..common.permissions import IsActiveAuthenticated
from ..common.redaction import safe_exception_message
from ..jobs.serializers import AsyncJobSerializer
from ..services.rag_service import (
    SYSTEM_CONTROLS,
    answer_document_query,
    run_document_controls,
)
from .models import AnalysisControl, DocumentAnalysisRun
from .selectors import visible_documents
from .serializers import (
    AnalysisControlSerializer,
    DocumentAnalysisRunSerializer,
    DocumentControlRunSerializer,
    DocumentDetailSerializer,
    DocumentListSerializer,
    DocumentRagQuerySerializer,
    DocumentUploadSerializer,
)
from .services.ingestion import ingest_document
from .services.lifecycle import delete_document

logger = logging.getLogger(__name__)
RUN_ERROR_MAX_LENGTH = 4000


def _persist_run_failure(run, exc):
    run.status = DocumentAnalysisRun.STATUS_FAILED
    run.error_message = safe_exception_message(exc, max_length=RUN_ERROR_MAX_LENGTH)
    run.completed_at = timezone.now()
    run.save(update_fields=["status", "error_message", "completed_at"])


class DocumentListView(generics.ListAPIView):
    permission_classes = [IsActiveAuthenticated]
    serializer_class = DocumentListSerializer

    def get_queryset(self):
        return visible_documents(self.request.user)[:50]


class DocumentDetailView(generics.RetrieveDestroyAPIView):
    permission_classes = [IsActiveAuthenticated]
    serializer_class = DocumentDetailSerializer
    lookup_url_kwarg = "document_id"

    def get_queryset(self):
        return visible_documents(self.request.user)

    def perform_destroy(self, instance):
        delete_document(document=instance)


class DocumentUploadView(APIView):
    permission_classes = [IsActiveAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = DocumentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ingestion = ingest_document(
            upload=serializer.validated_data["file"],
            prompt=serializer.validated_data["prompt"],
            use_ocr=serializer.validated_data["use_ocr"],
            use_ai=serializer.validated_data["use_ai"],
            owner=request.user,
        )
        return Response(
            {
                "job": AsyncJobSerializer(ingestion.job).data,
                "document": DocumentDetailSerializer(ingestion.document).data,
            },
            status=status.HTTP_202_ACCEPTED,
        )


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
        document = generics.get_object_or_404(visible_documents(request.user), pk=document_id)
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
            safe_error = safe_exception_message(exc, max_length=RUN_ERROR_MAX_LENGTH)
            logger.error(
                "RAG query failed: %s",
                safe_error,
                extra={"event": "document_rag_failed", "document_id": document.pk},
            )
            _persist_run_failure(run, exc)
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
        document = generics.get_object_or_404(visible_documents(request.user), pk=document_id)
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
            safe_error = safe_exception_message(exc, max_length=RUN_ERROR_MAX_LENGTH)
            logger.warning(
                "Document control request rejected: %s",
                safe_error,
                extra={"event": "document_control_rejected", "document_id": document.pk},
            )
            _persist_run_failure(run, exc)
            return Response(
                {"detail": "Doküman kontrol isteği geçersiz.", "run_id": run.pk},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as exc:
            safe_error = safe_exception_message(exc, max_length=RUN_ERROR_MAX_LENGTH)
            logger.error(
                "Document controls failed: %s",
                safe_error,
                extra={"event": "document_controls_failed", "document_id": document.pk},
            )
            _persist_run_failure(run, exc)
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
        document = generics.get_object_or_404(
            visible_documents(self.request.user),
            pk=self.kwargs["document_id"],
        )
        runs = document.analysis_runs.all()
        if not self.request.user.is_staff:
            runs = runs.filter(created_by=self.request.user)
        return runs[:25]
