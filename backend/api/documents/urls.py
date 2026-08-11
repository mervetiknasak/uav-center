from django.urls import path

from .views import (
    DocumentAnalysisRunListView,
    DocumentControlRunView,
    DocumentDetailView,
    DocumentListView,
    DocumentRagQueryView,
    DocumentUploadView,
)

urlpatterns = [
    path("", DocumentListView.as_view(), name="document-list"),
    path("upload/", DocumentUploadView.as_view(), name="document-upload"),
    path("<int:document_id>/", DocumentDetailView.as_view(), name="document-detail"),
    path("<int:document_id>/rag/query/", DocumentRagQueryView.as_view(), name="document-rag-query"),
    path(
        "<int:document_id>/analyses/",
        DocumentAnalysisRunListView.as_view(),
        name="document-analysis-runs",
    ),
    path(
        "<int:document_id>/controls/run/",
        DocumentControlRunView.as_view(),
        name="document-control-run",
    ),
]
