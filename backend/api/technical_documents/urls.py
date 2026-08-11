from django.urls import path

from .views import (
    TechnicalDocumentDetailView,
    TechnicalDocumentListCreateView,
    TechnicalDocumentNotifyView,
)

urlpatterns = [
    path("", TechnicalDocumentListCreateView.as_view(), name="technical-document-list"),
    path(
        "<int:technical_document_id>/",
        TechnicalDocumentDetailView.as_view(),
        name="technical-document-detail",
    ),
    path(
        "<int:technical_document_id>/notify/",
        TechnicalDocumentNotifyView.as_view(),
        name="technical-document-notify",
    ),
]
