"""Transactional use cases for the technical-document aggregate."""

from collections.abc import Mapping
from typing import Any

from django.db import transaction

from ..models import CoverPage, TechnicalDocument, TechnicalDocumentStatusHistory

_COVER_PAGE_UNSET = object()


def _resolve_cover_page(project, cover_page_data):
    if cover_page_data is None:
        return None
    cover_page, _ = CoverPage.objects.get_or_create(
        project=project,
        number=cover_page_data["number"].strip(),
        issue=cover_page_data["issue"].strip(),
    )
    return cover_page


@transaction.atomic
def create_technical_document(
    *,
    validated_data: Mapping[str, Any],
    actor,
) -> TechnicalDocument:
    """Create a document and its initial audit record as one unit of work."""

    data = dict(validated_data)
    panels = data.pop("panels", [])
    cover_page_data = data.pop("cover_page", None)
    data.pop("status_note", None)
    document = TechnicalDocument.objects.create(
        **data,
        cover_page=_resolve_cover_page(data["project"], cover_page_data),
        created_by=actor,
        updated_by=actor,
    )
    document.panels.set(panels)
    TechnicalDocumentStatusHistory.objects.create(
        document=document,
        to_status=document.status,
        note="Doküman kaydı oluşturuldu.",
        changed_by=actor,
    )
    return document


@transaction.atomic
def update_technical_document(
    *,
    document: TechnicalDocument,
    validated_data: Mapping[str, Any],
    actor,
) -> TechnicalDocument:
    """Update aggregate relations and status history atomically."""

    data = dict(validated_data)
    panels = data.pop("panels", None)
    cover_page_data = data.pop("cover_page", _COVER_PAGE_UNSET)
    status_note = data.pop("status_note", "")
    previous_status = document.status

    for field, value in data.items():
        setattr(document, field, value)
    if cover_page_data is not _COVER_PAGE_UNSET:
        document.cover_page = _resolve_cover_page(document.project, cover_page_data)
    document.updated_by = actor
    document.save()

    if panels is not None:
        document.panels.set(panels)
    if previous_status != document.status:
        TechnicalDocumentStatusHistory.objects.create(
            document=document,
            from_status=previous_status,
            to_status=document.status,
            note=status_note,
            changed_by=actor,
        )
    return document
