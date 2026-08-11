from pathlib import Path

from django.db.models import Q
from django.http import FileResponse
from rest_framework import generics
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from ..common.permissions import IsActiveAuthenticated
from ..services.flight_permit_document import build_flight_permit_document
from .file_policy import document_content_type
from .models import FlightPermit
from .selectors import flight_permits_with_actors
from .serializers import FlightPermitSerializer
from .services.lifecycle import delete_flight_permit


class FlightPermitListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsActiveAuthenticated]
    serializer_class = FlightPermitSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        queryset = flight_permits_with_actors()
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
    queryset = flight_permits_with_actors()
    lookup_url_kwarg = "flight_permit_id"

    def perform_destroy(self, instance):
        delete_flight_permit(permit=instance)


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
            content_type=document_content_type(
                permit.document_name or Path(permit.document.name).name
            ),
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
