import logging
from collections.abc import Mapping
from typing import Any

from django.db import IntegrityError, transaction
from django.utils import timezone

from ..common.redaction import safe_exception_message
from .file_policy import presentation_content_type
from .models import EDKApplication

logger = logging.getLogger(__name__)


class EDKApplicationConflict(Exception):
    pass


class EDKJiraConflict(Exception):
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


def link_edk_jira_issue(*, application, issue_key, url, summary):
    """Persist the stable EDK-to-Jira identity before any optional status refresh."""

    try:
        with transaction.atomic():
            locked = EDKApplication.objects.select_for_update().get(pk=application.pk)
            if locked.jira_issue_key and locked.jira_issue_key != issue_key:
                raise EDKJiraConflict("Bu EDK başka bir Jira Task'ına bağlı.")
            first_link = not locked.jira_issue_key
            locked.jira_issue_key = str(issue_key)[:64]
            locked.jira_url = str(url)[:500]
            locked.jira_summary = str(summary)[:500]
            update_fields = ["jira_issue_key", "jira_url", "jira_summary", "updated_at"]
            if first_link:
                locked.jira_status = ""
                locked.jira_subtasks = []
                locked.jira_last_synced_at = None
                update_fields.extend(["jira_status", "jira_subtasks", "jira_last_synced_at"])
            locked.save(update_fields=update_fields)
            return locked
    except IntegrityError as exc:
        raise EDKJiraConflict("Bu Jira Task'ı başka bir EDK ile bağlantılı.") from exc


@transaction.atomic
def record_edk_jira_tracking(*, application, tracking):
    """Store one validated Jira snapshot without holding a lock during HTTP I/O."""

    locked = EDKApplication.objects.select_for_update().get(pk=application.pk)
    if not locked.jira_issue_key or locked.jira_issue_key != tracking["key"]:
        raise EDKJiraConflict("EDK Jira bağlantısı senkronizasyon sırasında değişti.")
    locked.jira_url = str(tracking["url"])[:500]
    locked.jira_summary = str(tracking["summary"])[:500]
    locked.jira_status = str(tracking["status"])[:120]
    locked.jira_subtasks = [
        {
            "key": str(item["key"])[:64],
            "url": str(item["url"])[:500],
            "summary": str(item["summary"])[:500],
            "status": str(item["status"])[:120],
            "is_closed": bool(item["is_closed"]),
        }
        for item in tracking["subtasks"]
    ]
    locked.jira_last_synced_at = timezone.now()
    locked.save(
        update_fields=[
            "jira_url",
            "jira_summary",
            "jira_status",
            "jira_subtasks",
            "jira_last_synced_at",
            "updated_at",
        ]
    )
    return locked


def jira_tracking_payload(application):
    if not application.jira_issue_key:
        return None
    subtasks = application.jira_subtasks if isinstance(application.jira_subtasks, list) else []
    closed_count = sum(
        1 for item in subtasks if isinstance(item, Mapping) and item.get("is_closed") is True
    )
    return {
        "key": application.jira_issue_key,
        "url": application.jira_url,
        "summary": application.jira_summary,
        "status": application.jira_status,
        "subtasks": subtasks,
        "subtask_total": len(subtasks),
        "subtask_closed": closed_count,
        "all_subtasks_closed": bool(subtasks) and closed_count == len(subtasks),
        "last_synced_at": application.jira_last_synced_at,
    }
