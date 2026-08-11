"""Atomic document-ingestion use case with storage compensation."""

import logging
from collections.abc import Callable
from dataclasses import dataclass

from django.db import transaction

from ...common.redaction import safe_exception_message
from ...jobs.models import AsyncJob
from ...services.job_queue import enqueue_document_processing
from ..models import Document

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DocumentIngestion:
    document: Document
    job: AsyncJob


def _delete_committed_upload(document: Document | None) -> None:
    if document is None:
        return
    stored_file = document.file
    if not stored_file or not stored_file.name or not stored_file._committed:
        return
    try:
        stored_file.storage.delete(stored_file.name)
    except Exception as exc:
        logger.error(
            "Rolled-back document upload cleanup failed: %s",
            safe_exception_message(exc),
            extra={
                "event": "document_upload_cleanup_failed",
                "document_id": document.pk,
            },
        )


def ingest_document(
    *,
    upload,
    prompt: str,
    use_ocr: bool,
    use_ai: bool,
    owner,
    enqueue: Callable[..., AsyncJob] | None = None,
) -> DocumentIngestion:
    """Persist the document and queue record as one database unit of work.

    File storage is not transactional. If either the queue insert or database
    commit fails after the upload is stored, an explicit compensation removes
    the orphaned object before the original exception is re-raised.
    """

    enqueue_job = enqueue or enqueue_document_processing
    document = None
    try:
        with transaction.atomic():
            document = Document(
                original_name=upload.name,
                file=upload,
                owner=owner,
                content_type=upload.content_type or "",
                size=upload.size,
                prompt=prompt,
            )
            document.save()
            job = enqueue_job(
                document=document,
                owner=owner,
                use_ocr=use_ocr,
                use_ai=use_ai,
            )
        return DocumentIngestion(document=document, job=job)
    except Exception:
        _delete_committed_upload(document)
        raise
