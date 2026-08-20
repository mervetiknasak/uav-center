from django.urls import path

from .views import (
    FormProcessAttachmentView,
    FormProcessGeneratedDocumentView,
    FormProcessRecordDetailView,
    FormProcessRecordListCreateView,
    FormProcessTemplateCatalogView,
)

urlpatterns = [
    path("templates/", FormProcessTemplateCatalogView.as_view(), name="form-process-templates"),
    path("", FormProcessRecordListCreateView.as_view(), name="form-process-record-list"),
    path(
        "<int:record_id>/", FormProcessRecordDetailView.as_view(), name="form-process-record-detail"
    ),
    path(
        "<int:record_id>/generated-document/",
        FormProcessGeneratedDocumentView.as_view(),
        name="form-process-generated-document",
    ),
    path(
        "<int:record_id>/attachment/",
        FormProcessAttachmentView.as_view(),
        name="form-process-attachment",
    ),
]
