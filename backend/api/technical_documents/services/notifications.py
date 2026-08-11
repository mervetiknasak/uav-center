"""Technical-document notification orchestration and audit persistence."""

from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from ...common.redaction import DEFAULT_SAFE_ERROR_MAX_LENGTH, safe_exception_message
from ..models import TechnicalDocument, TechnicalDocumentNotification
from ..ports import EmailSender

MAX_AUDIT_ERROR_LENGTH = DEFAULT_SAFE_ERROR_MAX_LENGTH


class NoNotificationRecipients(ValueError):
    """Raised when a document has no panel responsible with an e-mail address."""


class NotificationDeliveryError(RuntimeError):
    """Raised after a failed delivery has been recorded in the audit log."""

    def __init__(self, notification: TechnicalDocumentNotification):
        super().__init__(notification.error_message)
        self.notification = notification


class NotificationInProgress(RuntimeError):
    """Raised when another request already owns the same delivery key."""


class NotificationKeyConflict(ValueError):
    """Raised when one idempotency key is reused for a different request payload."""


class NotificationOutcomeUnknown(RuntimeError):
    """Raised when a stale claim cannot be safely replayed through SMTP."""

    def __init__(self, notification: TechnicalDocumentNotification):
        super().__init__(notification.error_message)
        self.notification = notification


@dataclass(frozen=True)
class NotificationResult:
    notification: TechnicalDocumentNotification
    recipient_count: int
    deduplicated: bool = False


def _recipients_for(document: TechnicalDocument) -> list[str]:
    return sorted(
        {
            responsible.email.strip().lower()
            for panel in document.panels.all()
            for responsible in panel.responsibles.all()
            if responsible.email.strip()
        }
    )


def _default_subject(document: TechnicalDocument) -> str:
    return f"[{document.project.code}] {document.code} — {document.title}"


def _default_message(document: TechnicalDocument) -> str:
    return (
        f"{document.code} kodlu “{document.title}” dokümanı için bilgilendirme.\n\n"
        f"Durum: {document.get_status_display()}\n"
        f"Revizyon: {document.revision}\n"
        f"Yayın tarihi: {document.publication_date or '—'}\n"
        f"Termin: {document.due_date or '—'}\n\n"
        "Bu ileti UAV Center Teknik Doküman Yönetimi üzerinden gönderilmiştir."
    )


def _resolve_stale_pending_claim(notification: TechnicalDocumentNotification) -> None:
    stale_before = timezone.now() - timedelta(
        seconds=settings.TECHNICAL_NOTIFICATION_PENDING_TIMEOUT
    )
    if notification.created_at > stale_before:
        return

    TechnicalDocumentNotification.objects.filter(
        pk=notification.pk,
        status=TechnicalDocumentNotification.STATUS_PENDING,
    ).update(
        status=TechnicalDocumentNotification.STATUS_UNKNOWN,
        error_message=(
            "Teslim sonucu süreç kesintisi nedeniyle doğrulanamadı; "
            "yeni gönderimden önce operasyonel uzlaştırma gerekir."
        ),
    )
    notification.refresh_from_db(fields=["status", "error_message"])


def send_document_notification(
    *,
    document: TechnicalDocument,
    actor,
    sender: EmailSender,
    idempotency_key: str,
    subject: str = "",
    message: str = "",
) -> NotificationResult:
    """Send outside a DB transaction, then atomically persist success metadata.

    A failed infrastructure call is also persisted as an audit entry before a
    typed application error is raised for HTTP-layer mapping.
    """

    recipients = _recipients_for(document)
    if not recipients:
        raise NoNotificationRecipients

    resolved_subject = subject.strip() or _default_subject(document)
    resolved_message = message.strip() or _default_message(document)
    with transaction.atomic():
        notification, created = TechnicalDocumentNotification.objects.get_or_create(
            document=document,
            idempotency_key=idempotency_key,
            defaults={
                "subject": resolved_subject,
                "message": resolved_message,
                "recipients": recipients,
                "recipient_count": len(recipients),
                "status": TechnicalDocumentNotification.STATUS_PENDING,
                "sent_by": actor,
            },
        )

    if not created:
        if (
            notification.subject != resolved_subject
            or notification.message != resolved_message
            or notification.recipients != recipients
        ):
            raise NotificationKeyConflict
        if notification.status == TechnicalDocumentNotification.STATUS_PENDING:
            _resolve_stale_pending_claim(notification)
        if notification.status == TechnicalDocumentNotification.STATUS_SENT:
            return NotificationResult(
                notification=notification,
                recipient_count=notification.recipient_count,
                deduplicated=True,
            )
        if notification.status == TechnicalDocumentNotification.STATUS_FAILED:
            raise NotificationDeliveryError(notification)
        if notification.status == TechnicalDocumentNotification.STATUS_UNKNOWN:
            raise NotificationOutcomeUnknown(notification)
        raise NotificationInProgress

    try:
        sender.send(
            subject=resolved_subject,
            body=resolved_message,
            bcc=recipients,
        )
    except Exception as exc:
        notification.status = TechnicalDocumentNotification.STATUS_FAILED
        notification.error_message = safe_exception_message(
            exc,
            max_length=MAX_AUDIT_ERROR_LENGTH,
        )
        with transaction.atomic():
            notification.save(update_fields=["status", "error_message"])
        raise NotificationDeliveryError(notification) from exc

    with transaction.atomic():
        notification.status = TechnicalDocumentNotification.STATUS_SENT
        notification.save(update_fields=["status"])
        TechnicalDocument.objects.filter(pk=document.pk).update(
            last_notification_at=notification.created_at,
            last_notification_recipient_count=len(recipients),
        )

    return NotificationResult(
        notification=notification,
        recipient_count=len(recipients),
    )
