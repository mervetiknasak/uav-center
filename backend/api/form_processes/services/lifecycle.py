"""Persistence use cases for shared engineering form records."""

from collections.abc import Mapping
from typing import Any

from django.db import transaction

from ..models import FormProcessRecord


def create_form_process_record(*, validated_data: Mapping[str, Any], actor) -> FormProcessRecord:
    with transaction.atomic():
        return FormProcessRecord.objects.create(
            **validated_data,
            created_by=actor,
            updated_by=actor,
        )


def update_form_process_record(
    *,
    record: FormProcessRecord,
    validated_data: Mapping[str, Any],
    actor,
) -> FormProcessRecord:
    with transaction.atomic():
        for field, value in validated_data.items():
            setattr(record, field, value)
        record.updated_by = actor
        record.save()
    return record
