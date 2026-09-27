import json
import logging
import re

from django.db import IntegrityError
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from ...common.permissions import IsActiveAdminUser, IsActiveAuthenticated
from ..models import FormNumberMapping
from ..serializers import FormProcessRecordSerializer
from . import client
from .serializers import AllocationInputSerializer, MappingSerializer
from .workflow import AllocationConflict, run_allocation, start_allocation, visible_allocation


def allocation_response(allocation):
    return {
        "id": str(allocation.pk),
        "status": allocation.status,
        "target_field": allocation.target_field,
        "document_number": allocation.document_number,
        "record": FormProcessRecordSerializer(allocation.record).data
        if allocation.record
        else None,
    }


class FormatsView(APIView):
    permission_classes = [IsActiveAdminUser]

    def get(self, request):
        try:
            page = int(request.query_params.get("page", 1))
            if not 1 <= page <= 10000:
                raise ValueError
        except ValueError as exc:
            raise ValidationError({"page": "Geçerli sayfa numarası girin."}) from exc
        return Response(client.list_formats(page))


class MappingPermissionsMixin:
    request: Request

    def get_permissions(self):
        permission = (
            IsActiveAuthenticated
            if self.request.method in {"GET", "HEAD", "OPTIONS"}
            else IsActiveAdminUser
        )
        return [permission()]

    def perform_create(self, serializer):
        self._save(serializer)

    def perform_update(self, serializer):
        self._save(serializer)

    def _save(self, serializer):
        try:
            serializer.save()
        except IntegrityError as exc:
            raise AllocationConflict("Bu form alanı için eşleştirme zaten var.") from exc


class MappingsView(MappingPermissionsMixin, generics.ListCreateAPIView):
    serializer_class = MappingSerializer
    pagination_class = None

    def get_queryset(self):
        query = FormNumberMapping.objects.all()
        if not self.request.user.is_staff:
            query = query.filter(enabled=True)
        template = self.request.query_params.get("template_code")
        return query.filter(template_code=template) if template else query


class MappingDetailView(MappingPermissionsMixin, generics.RetrieveUpdateAPIView):
    serializer_class = MappingSerializer
    queryset = FormNumberMapping.objects.all()
    http_method_names = ["get", "patch", "head", "options"]


class AllocationsView(APIView):
    permission_classes = [IsActiveAuthenticated]
    parser_classes = [JSONParser, MultiPartParser]

    def post(self, request):
        key = request.headers.get("Idempotency-Key", "")
        if not re.fullmatch(r"[A-Za-z0-9._:-]{1,128}", key):
            raise ValidationError({"idempotency_key": "Geçerli Idempotency-Key zorunludur."})
        data = request.data
        if "payload" in request.data:
            try:
                data = json.loads(request.data["payload"])
            except (TypeError, ValueError) as exc:
                raise ValidationError("Geçersiz JSON form verisi.") from exc
        serializer = AllocationInputSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        allocation, created = start_allocation(
            actor=request.user,
            key=key,
            payload=serializer.validated_data,
            attachment=request.FILES.get("attachment"),
        )
        return execute(allocation, created)


def execute(allocation, created=False):
    try:
        allocation = run_allocation(allocation)
    except (client.NumberingUnavailable, AllocationConflict, ValidationError) as exc:
        allocation.refresh_from_db()
        return Response(
            {
                "detail": exc.detail,
                "allocation_id": str(allocation.pk),
                "status": allocation.status,
            },
            status=exc.status_code,
        )
    except Exception:
        logging.getLogger(__name__).error(
            "Form number allocation needs recovery",
            extra={"event": "form_number_allocation_failed", "allocation_id": str(allocation.pk)},
        )
        return Response(
            {
                "detail": "Numara işlemi kaydedilemedi. Aynı işlemi tekrar deneyin.",
                "allocation_id": str(allocation.pk),
            },
            status=502,
        )
    return Response(allocation_response(allocation), status=201 if created else 200)


class AllocationDetailView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def get(self, request, allocation_id):
        return Response(allocation_response(visible_allocation(request.user, allocation_id)))


class AllocationRetryView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def post(self, request, allocation_id):
        allocation = visible_allocation(request.user, allocation_id)
        # A retry writes the initiator's snapshot; only that actor or an administrator may do it.
        if allocation.created_by_id != request.user.pk and not request.user.is_staff:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied()
        return execute(allocation)
