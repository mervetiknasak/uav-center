from django.urls import path

from .views import DocumentDetailView, DocumentListView, DocumentUploadView, health_check

urlpatterns = [
    path("health/", health_check, name="health-check"),
    path("documents/", DocumentListView.as_view(), name="document-list"),
    path("documents/upload/", DocumentUploadView.as_view(), name="document-upload"),
    path("documents/<int:document_id>/", DocumentDetailView.as_view(), name="document-detail"),
]
