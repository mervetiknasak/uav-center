from django.urls import path

from .views import (
    FlightPermitDetailView,
    FlightPermitDocumentView,
    FlightPermitGeneratedDocumentView,
    FlightPermitListCreateView,
    FlightPermitTemplateCatalogView,
)

urlpatterns = [
    path("templates/", FlightPermitTemplateCatalogView.as_view(), name="flight-permit-templates"),
    path("", FlightPermitListCreateView.as_view(), name="flight-permit-list"),
    path("<int:flight_permit_id>/", FlightPermitDetailView.as_view(), name="flight-permit-detail"),
    path(
        "<int:flight_permit_id>/document/",
        FlightPermitDocumentView.as_view(),
        name="flight-permit-document",
    ),
    path(
        "<int:flight_permit_id>/generated-document/",
        FlightPermitGeneratedDocumentView.as_view(),
        name="flight-permit-generated-document",
    ),
]
