"""Flight-permit persistence and stored-file lifecycle use cases."""

import logging
from collections.abc import Mapping
from functools import partial
from typing import Any

from django.db import transaction

from ...common.redaction import safe_exception_message
from ..file_policy import document_content_type
from ..models import FlightPermit

logger = logging.getLogger(__name__)


def _document_metadata(uploaded_file) -> dict[str, Any]:
    return {
        "document_name": uploaded_file.name,
        "document_content_type": document_content_type(uploaded_file.name),
        "document_size": uploaded_file.size,
    }


def _stored_document(permit: FlightPermit):
    if not permit.document:
        return None, ""
    return permit.document.storage, permit.document.name


def _delete_stored_document(storage, stored_name: str, *, permit_id: int | None) -> None:
    try:
        storage.delete(stored_name)
    except Exception as exc:
        logger.error(
            "Flight-permit storage cleanup failed: %s",
            safe_exception_message(exc),
            extra={
                "event": "flight_permit_storage_cleanup_failed",
                "flight_permit_id": permit_id,
            },
        )


def _compensate_new_upload(permit: FlightPermit, *, previous_name: str = "") -> None:
    stored_file = permit.document
    if (
        not stored_file
        or not stored_file.name
        or not stored_file._committed
        or stored_file.name == previous_name
    ):
        return
    _delete_stored_document(
        stored_file.storage,
        stored_file.name,
        permit_id=permit.pk,
    )


def create_flight_permit(
    *,
    validated_data: Mapping[str, Any],
    actor,
) -> FlightPermit:
    data = dict(validated_data)
    data.pop("remove_document", None)
    upload = data.get("document")
    if upload:
        data.update(_document_metadata(upload))
    permit = FlightPermit(
        **data,
        created_by=actor,
        updated_by=actor,
    )
    try:
        with transaction.atomic():
            permit.save()
    except Exception:
        _compensate_new_upload(permit)
        raise
    return permit


def update_flight_permit(
    *,
    permit: FlightPermit,
    validated_data: Mapping[str, Any],
    actor,
) -> FlightPermit:
    data = dict(validated_data)
    remove_document = data.pop("remove_document", False)
    upload = data.get("document")
    old_storage, old_document_name = _stored_document(permit)

    if upload:
        data.update(_document_metadata(upload))
    elif remove_document:
        data.update(
            {
                "document": None,
                "document_name": "",
                "document_content_type": "",
                "document_size": 0,
            }
        )

    try:
        with transaction.atomic():
            for field, value in data.items():
                setattr(permit, field, value)
            permit.updated_by = actor
            permit.save()

            if old_storage and old_document_name and (upload or remove_document):
                transaction.on_commit(
                    partial(
                        _delete_stored_document,
                        old_storage,
                        old_document_name,
                        permit_id=permit.pk,
                    )
                )
    except Exception:
        if upload:
            _compensate_new_upload(permit, previous_name=old_document_name)
        raise
    return permit


def delete_flight_permit(*, permit: FlightPermit) -> None:
    storage, document_name = _stored_document(permit)
    permit_id = permit.pk
    with transaction.atomic():
        permit.delete()
        if storage and document_name:
            transaction.on_commit(
                partial(
                    _delete_stored_document,
                    storage,
                    document_name,
                    permit_id=permit_id,
                )
            )
