"""Document aggregate lifecycle operations."""

import logging
from functools import partial

from django.db import transaction

from ...common.redaction import safe_exception_message
from ..models import Document

logger = logging.getLogger(__name__)


def _delete_stored_file(storage, stored_name: str, *, document_id: int) -> None:
    try:
        storage.delete(stored_name)
    except Exception as exc:
        logger.error(
            "Deleted document storage cleanup failed: %s",
            safe_exception_message(exc),
            extra={
                "event": "document_storage_cleanup_failed",
                "document_id": document_id,
            },
        )


def delete_document(*, document: Document) -> None:
    """Delete the DB aggregate before removing its file after commit."""

    document_id = document.pk
    storage = document.file.storage if document.file else None
    stored_name = document.file.name if document.file else ""
    with transaction.atomic():
        document.delete()
        if storage and stored_name:
            transaction.on_commit(
                partial(
                    _delete_stored_file,
                    storage,
                    stored_name,
                    document_id=document_id,
                )
            )
