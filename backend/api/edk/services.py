from django.db import transaction
from django.utils import timezone

from .models import EDKApplication


class EDKApplicationConflict(Exception):
    pass


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
