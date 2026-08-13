from django.db.models import Q
from django.http import FileResponse
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from ..common.permissions import IsActiveAuthenticated
from .catalog import form_process_catalog
from .models import FormProcessRecord
from .selectors import form_process_records_with_actors
from .serializers import FormProcessRecordSerializer
from .services.documents import build_form_process_document


class FormProcessTemplateCatalogView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def get(self, request):
        return Response(form_process_catalog())


class FormProcessRecordListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsActiveAuthenticated]
    serializer_class = FormProcessRecordSerializer

    def get_queryset(self):
        queryset = form_process_records_with_actors()
        process_code = self.request.query_params.get("process", "").strip()
        template_code = self.request.query_params.get("template", "").strip()
        status_value = self.request.query_params.get("status", "").strip()
        search = self.request.query_params.get("search", "").strip()
        if process_code:
            queryset = queryset.filter(process_code=process_code)
        if template_code:
            queryset = queryset.filter(template_code=template_code)
        if status_value:
            queryset = queryset.filter(status=status_value)
        if search:
            queryset = queryset.filter(
                Q(record_number__icontains=search) | Q(title__icontains=search)
            )
        return queryset


class FormProcessRecordDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsActiveAuthenticated]
    serializer_class = FormProcessRecordSerializer
    queryset = form_process_records_with_actors()
    lookup_url_kwarg = "record_id"


class FormProcessGeneratedDocumentView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def get(self, request, record_id):
        record = generics.get_object_or_404(FormProcessRecord, pk=record_id)
        document = build_form_process_document(record)
        safe_number = "".join(
            character if character.isalnum() or character in {"-", "_"} else "_"
            for character in record.record_number
        )
        response = FileResponse(
            document,
            as_attachment=True,
            filename=f"{record.template_code}_{safe_number}.docx",
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        response["X-Content-Type-Options"] = "nosniff"
        return response
