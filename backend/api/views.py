"""Backwards-compatible view imports owned by feature packages."""

from .accounts.views import (
    AdminUserListView,
    AdminUserStatusView,
    CsrfTokenView,
    CurrentUserView,
    LoginView,
    LogoutView,
    RegisterView,
)
from .ai.views import OllamaChatView, OllamaPullView, OllamaStatusView, OllamaUnloadView
from .common.permissions import IsActiveAdminUser, IsActiveAuthenticated
from .common.readiness import readiness_check
from .common.views import health_check
from .documents.views import (
    AnalysisControlDetailView,
    AnalysisControlListCreateView,
    DocumentAnalysisRunListView,
    DocumentControlRunView,
    DocumentDetailView,
    DocumentListView,
    DocumentRagQueryView,
    DocumentUploadView,
)
from .jobs.views import AsyncJobCancelView, AsyncJobDetailView, AsyncJobListView
from .organization.permissions import IsOrganizationReaderOrAdmin
from .organization.views import (
    GroupPersonListCreateView,
    PanelResponsibleDetailView,
    PanelResponsibleListCreateView,
    PersonDetailView,
    PersonGroupDetailView,
    PersonGroupListCreateView,
    ProjectDetailView,
    ProjectListCreateView,
    ProjectPanelDetailView,
    ProjectPanelListCreateView,
)
from .services.ai_processor import process_document_text
from .technical_documents.selectors import technical_document_queryset
from .technical_documents.views import (
    TechnicalDocumentDetailView,
    TechnicalDocumentListCreateView,
    TechnicalDocumentNotifyView,
)

__all__ = [
    "AdminUserListView",
    "AdminUserStatusView",
    "AnalysisControlDetailView",
    "AnalysisControlListCreateView",
    "AsyncJobCancelView",
    "AsyncJobDetailView",
    "AsyncJobListView",
    "CsrfTokenView",
    "CurrentUserView",
    "DocumentAnalysisRunListView",
    "DocumentControlRunView",
    "DocumentDetailView",
    "DocumentListView",
    "DocumentRagQueryView",
    "DocumentUploadView",
    "GroupPersonListCreateView",
    "IsActiveAdminUser",
    "IsActiveAuthenticated",
    "IsOrganizationReaderOrAdmin",
    "LoginView",
    "LogoutView",
    "OllamaChatView",
    "OllamaPullView",
    "OllamaStatusView",
    "OllamaUnloadView",
    "PanelResponsibleDetailView",
    "PanelResponsibleListCreateView",
    "PersonDetailView",
    "PersonGroupDetailView",
    "PersonGroupListCreateView",
    "ProjectDetailView",
    "ProjectListCreateView",
    "ProjectPanelDetailView",
    "ProjectPanelListCreateView",
    "RegisterView",
    "TechnicalDocumentDetailView",
    "TechnicalDocumentListCreateView",
    "TechnicalDocumentNotifyView",
    "health_check",
    "readiness_check",
    "process_document_text",
    "technical_document_queryset",
]
