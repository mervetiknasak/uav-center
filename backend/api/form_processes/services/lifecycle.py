"""Persistence and attachment lifecycle for shared engineering form records."""

import logging
from collections.abc import Mapping
from functools import partial
from typing import Any

from django.db import transaction

from ...common.redaction import safe_exception_message
from ..file_policy import attachment_content_type
from ..models import FormProcessRecord

logger = logging.getLogger(__name__)


def _attachment_metadata(uploaded_file) -> dict[str, Any]:
    return {
        "attachment_name": uploaded_file.name,
        "attachment_content_type": attachment_content_type(uploaded_file.name),
        "attachment_size": uploaded_file.size,
    }


def _stored_attachment(record: FormProcessRecord):
    if not record.attachment:
        return None, ""
    return record.attachment.storage, record.attachment.name


def _delete_stored_attachment(storage, stored_name: str, *, record_id: int | None) -> None:
    try:
        storage.delete(stored_name)
    except Exception as exc:
        logger.error(
            "Form-process attachment cleanup failed: %s",
            safe_exception_message(exc),
            extra={
                "event": "form_process_attachment_cleanup_failed",
                "form_process_record_id": record_id,
            },
        )


def _compensate_new_upload(record: FormProcessRecord, *, previous_name: str = "") -> None:
    stored_file = record.attachment
    if (
        not stored_file
        or not stored_file.name
        or not stored_file._committed
        or stored_file.name == previous_name
    ):
        return
    _delete_stored_attachment(
        stored_file.storage,
        stored_file.name,
        record_id=record.pk,
    )


def create_form_process_record(*, validated_data: Mapping[str, Any], actor) -> FormProcessRecord:
    data = dict(validated_data)
    data.pop("remove_attachment", None)
    upload = data.get("attachment")
    if upload:
        data.update(_attachment_metadata(upload))
    record = FormProcessRecord(
        **data,
        created_by=actor,
        updated_by=actor,
    )
    try:
        with transaction.atomic():
            record.save()
    except Exception:
        _compensate_new_upload(record)
        raise
    return record


def update_form_process_record(
    *,
    record: FormProcessRecord,
    validated_data: Mapping[str, Any],
    actor,
) -> FormProcessRecord:
    data = dict(validated_data)
    remove_attachment = data.pop("remove_attachment", False)
    upload = data.get("attachment")
    old_storage, old_attachment_name = _stored_attachment(record)

    if upload:
        data.update(_attachment_metadata(upload))
    elif remove_attachment:
        data.update(
            {
                "attachment": None,
                "attachment_name": "",
                "attachment_content_type": "",
                "attachment_size": 0,
            }
        )

    try:
        with transaction.atomic():
            for field, value in data.items():
                setattr(record, field, value)
            record.updated_by = actor
            record.save()

            if old_storage and old_attachment_name and (upload or remove_attachment):
                transaction.on_commit(
                    partial(
                        _delete_stored_attachment,
                        old_storage,
                        old_attachment_name,
                        record_id=record.pk,
                    )
                )
    except Exception:
        if upload:
            _compensate_new_upload(record, previous_name=old_attachment_name)
        raise
    return record


def delete_form_process_record(*, record: FormProcessRecord) -> None:
    storage, attachment_name = _stored_attachment(record)
    record_id = record.pk
    with transaction.atomic():
        record.delete()
        if storage and attachment_name:
            transaction.on_commit(
                partial(
                    _delete_stored_attachment,
                    storage,
                    attachment_name,
                    record_id=record_id,
                )
            )
