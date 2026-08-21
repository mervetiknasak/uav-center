import logging
from collections.abc import Mapping
from typing import Any

from django.db import transaction
from django.utils import timezone

from ..common.redaction import safe_exception_message
from .file_policy import presentation_content_type
from .models import EDKApplication

logger = logging.getLogger(__name__)


class EDKApplicationConflict(Exception):
    pass


def _delete_presentation(application):
    presentation = application.presentation
    if not presentation or not presentation.name or not presentation._committed:
        return
    try:
        presentation.storage.delete(presentation.name)
    except Exception as exc:
        logger.error(
            "EDK presentation cleanup failed: %s",
            safe_exception_message(exc),
            extra={
                "event": "edk_presentation_cleanup_failed",
                "edk_application_id": application.pk,
            },
        )


def create_edk_application(*, validated_data: Mapping[str, Any], applicant) -> EDKApplication:
    data = dict(validated_data)
    presentation = data.get("presentation")
    if presentation:
        data.update(
            {
                "presentation_file_name": presentation.name[:255],
                "presentation_content_type": presentation_content_type(presentation.name),
                "presentation_size": presentation.size,
            }
        )
    application = EDKApplication(applicant=applicant, **data)
    try:
        with transaction.atomic():
            application.save()
    except Exception:
        _delete_presentation(application)
        raise
    return application


@transaction.atomic
def decide_edk_application(*, application, reviewer, status, decision_note):
    locked = EDKApplication.objects.select_for_update().get(pk=application.pk)
    if locked.status != EDKApplication.STATUS_PENDING:
        raise EDKApplicationConflict("Bu başvuru daha önce karara bağlanmış.")
    if locked.applicant_id == reviewer.id:
        raise EDKApplicationConflict("Kullanıcı kendi EDK başvurusunu onaylayamaz.")

    locked.status = status
    locked.decision_note = decision_note
    locked.reviewed_by = reviewer
    locked.reviewed_at = timezone.now()
    locked.save(
        update_fields=[
            "status",
            "decision_note",
            "reviewed_by",
            "reviewed_at",
            "updated_at",
        ]
    )
    return locked


def record_minutes_upload(*, application, file_name):
    application.minutes_file_name = file_name[:255]
    application.minutes_uploaded_at = timezone.now()
    application.save(update_fields=["minutes_file_name", "minutes_uploaded_at", "updated_at"])
    return application
