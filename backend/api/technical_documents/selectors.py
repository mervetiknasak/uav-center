from django.db.models import Prefetch

from ..organization.models import ProjectPanel
from .models import TechnicalDocument


def technical_document_queryset():
    return TechnicalDocument.objects.select_related(
        "project",
        "cover_page",
        "created_by",
        "updated_by",
    ).prefetch_related(
        Prefetch(
            "panels",
            queryset=ProjectPanel.objects.prefetch_related("responsibles"),
        ),
        "status_history__changed_by",
        "notifications__sent_by",
    )
