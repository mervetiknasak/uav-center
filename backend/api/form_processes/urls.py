from django.urls import path

from .numbering.views import (
    AllocationDetailView,
    AllocationRetryView,
    AllocationsView,
    FormatsView,
    MappingDetailView,
    MappingsView,
)
from .views import (
    FormProcessAttachmentView,
    FormProcessGeneratedDocumentView,
    FormProcessRecordDetailView,
    FormProcessRecordListCreateView,
    FormProcessTemplateCatalogView,
)

urlpatterns = [
    path("numbering/formats/", FormatsView.as_view()),
    path("numbering/mappings/", MappingsView.as_view()),
    path("numbering/mappings/<int:pk>/", MappingDetailView.as_view()),
    path("numbering/allocations/", AllocationsView.as_view()),
    path("numbering/allocations/<uuid:allocation_id>/", AllocationDetailView.as_view()),
    path("numbering/allocations/<uuid:allocation_id>/retry/", AllocationRetryView.as_view()),
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
