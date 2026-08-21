from datetime import date, timedelta

from django.db.models import OuterRef, Prefetch, Q, Subquery

from ..organization.models import ProjectPanel
from .models import TechnicalDocument, TechnicalDocumentStatusHistory


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


def technical_document_operational_alert_candidates(
    *,
    as_of: date,
    horizon_days: int,
):
    """Return the bounded read model needed by the operational-alert service."""

    horizon = as_of + timedelta(days=horizon_days)
    due_terminal_statuses = {
        TechnicalDocument.STATUS_PUBLISHED,
        TechnicalDocument.STATUS_SUPERSEDED,
        TechnicalDocument.STATUS_ARCHIVED,
    }
    review_terminal_statuses = {
        TechnicalDocument.STATUS_SUPERSEDED,
        TechnicalDocument.STATUS_ARCHIVED,
    }
    workflow_statuses = {
        TechnicalDocument.STATUS_IN_REVIEW,
        TechnicalDocument.STATUS_CHANGES_REQUESTED,
    }
    latest_current_status_change = (
        TechnicalDocumentStatusHistory.objects.filter(
            document_id=OuterRef("pk"),
            to_status=OuterRef("status"),
        )
        .order_by("-created_at", "-pk")
        .values("created_at")[:1]
    )

    return (
        TechnicalDocument.objects.annotate(
            current_status_started_at=Subquery(latest_current_status_change),
        )
        .filter(
            (Q(due_date__lte=horizon) & ~Q(status__in=due_terminal_statuses))
            | (Q(review_date__lte=horizon) & ~Q(status__in=review_terminal_statuses))
            | Q(status__in=workflow_statuses)
        )
        .select_related("project")
        .prefetch_related(
            Prefetch(
                "panels",
                queryset=ProjectPanel.objects.only("id", "name").order_by("order", "name"),
            )
        )
        .order_by("pk")
    )
