"""Django model discovery and backwards-compatible public imports.

Feature packages own the model implementations.  Keeping this explicit façade
preserves the stable ``api.models`` import path and the existing ``api`` app
label used by historical migrations.
"""

from .documents.models import AnalysisControl, Document, DocumentAnalysisRun, DocumentChunk
from .flight_permits.models import FlightPermit
from .form_processes.models import FormProcessRecord
from .jobs.models import AsyncJob
from .organization.models import PanelResponsible, Person, PersonGroup, Project, ProjectPanel
from .technical_documents.models import (
    CoverPage,
    TechnicalDocument,
    TechnicalDocumentNotification,
    TechnicalDocumentStatusHistory,
)

__all__ = [
    "AnalysisControl",
    "AsyncJob",
    "CoverPage",
    "Document",
    "DocumentAnalysisRun",
    "DocumentChunk",
    "FlightPermit",
    "FormProcessRecord",
    "PanelResponsible",
    "Person",
    "PersonGroup",
    "Project",
    "ProjectPanel",
    "TechnicalDocument",
    "TechnicalDocumentNotification",
    "TechnicalDocumentStatusHistory",
]
