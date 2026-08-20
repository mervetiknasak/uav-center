"""Backwards-compatible serializer imports owned by feature packages."""

from .accounts.serializers import (
    AdminUserSerializer,
    AdminUserStatusSerializer,
    LoginSerializer,
    RegisterSerializer,
    UserSerializer,
)
from .ai.serializers import OllamaChatMessageSerializer, OllamaChatRequestSerializer
from .documents.serializers import (
    AnalysisControlSerializer,
    DocumentAnalysisRunSerializer,
    DocumentControlRunSerializer,
    DocumentDetailSerializer,
    DocumentListSerializer,
    DocumentRagQuerySerializer,
    DocumentUploadSerializer,
)
from .jobs.serializers import AsyncJobSerializer
from .meeting_minutes.serializers import WordToJiraPublishRequestSerializer
from .organization.serializers import (
    PanelResponsibleSerializer,
    PersonGroupSerializer,
    PersonSerializer,
    ProjectPanelSerializer,
    ProjectSerializer,
)
from .technical_documents.serializers import (
    CoverPageSerializer,
    TechnicalDocumentNotificationRequestSerializer,
    TechnicalDocumentNotificationSerializer,
    TechnicalDocumentPanelSerializer,
    TechnicalDocumentSerializer,
    TechnicalDocumentStatusHistorySerializer,
)

__all__ = [
    "AdminUserSerializer",
    "AdminUserStatusSerializer",
    "AnalysisControlSerializer",
    "AsyncJobSerializer",
    "CoverPageSerializer",
    "DocumentAnalysisRunSerializer",
    "DocumentControlRunSerializer",
    "DocumentDetailSerializer",
    "DocumentListSerializer",
    "DocumentRagQuerySerializer",
    "DocumentUploadSerializer",
    "LoginSerializer",
    "OllamaChatMessageSerializer",
    "OllamaChatRequestSerializer",
    "PanelResponsibleSerializer",
    "PersonGroupSerializer",
    "PersonSerializer",
    "ProjectPanelSerializer",
    "ProjectSerializer",
    "RegisterSerializer",
    "TechnicalDocumentNotificationRequestSerializer",
    "TechnicalDocumentNotificationSerializer",
    "TechnicalDocumentPanelSerializer",
    "TechnicalDocumentSerializer",
    "TechnicalDocumentStatusHistorySerializer",
    "UserSerializer",
    "WordToJiraPublishRequestSerializer",
]
