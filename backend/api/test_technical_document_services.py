from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TransactionTestCase, override_settings
from django.utils import timezone

from .models import (
    PanelResponsible,
    Project,
    ProjectPanel,
    TechnicalDocument,
    TechnicalDocumentNotification,
)
from .technical_documents.services.notifications import (
    MAX_AUDIT_ERROR_LENGTH,
    NotificationDeliveryError,
    NotificationInProgress,
    NotificationKeyConflict,
    NotificationOutcomeUnknown,
    send_document_notification,
)


class RecordingSender:
    def __init__(self, error=None):
        self.error = error
        self.calls = []
        self.called_inside_atomic_block = None

    def send(self, *, subject, body, bcc):
        self.called_inside_atomic_block = connection.in_atomic_block
        self.calls.append({"subject": subject, "body": body, "bcc": list(bcc)})
        if self.error:
            raise self.error


class TechnicalDocumentNotificationServiceTests(TransactionTestCase):
    def setUp(self):
        self.actor = get_user_model().objects.create_user(
            username="notification-admin",
            password="StrongPass123!",
            is_staff=True,
        )
        project = Project.objects.create(name="TULPAR", code="TPL")
        panel = ProjectPanel.objects.create(project=project, name="Aviyonik")
        PanelResponsible.objects.create(
            panel=panel,
            name="Ada Yılmaz",
            email="ADA@example.com",
        )
        self.document = TechnicalDocument.objects.create(
            project=project,
            code="TPL-NOTIFY-1",
            title="Bildirim Testi",
        )
        self.document.panels.add(panel)

    def test_sender_is_injected_and_called_outside_service_transaction(self):
        sender = RecordingSender()

        result = send_document_notification(
            document=self.document,
            actor=self.actor,
            sender=sender,
            idempotency_key="notification-test-0001",
            message="İnceleme için bilginize.",
        )

        self.assertFalse(sender.called_inside_atomic_block)
        self.assertEqual(sender.calls[0]["bcc"], ["ada@example.com"])
        self.assertEqual(result.notification.status, TechnicalDocumentNotification.STATUS_SENT)
        self.document.refresh_from_db()
        self.assertEqual(self.document.last_notification_recipient_count, 1)

    def test_delivery_failure_is_audited_with_truncated_redacted_error(self):
        unsafe_error = RuntimeError(
            "password=super-secret token=top-secret "
            "http://10.0.0.8:25/smtp /private/tmp/mail.txt "
            "sender@example.com " + ("x" * 2000)
        )
        sender = RecordingSender(error=unsafe_error)

        with self.assertRaises(NotificationDeliveryError):
            send_document_notification(
                document=self.document,
                actor=self.actor,
                sender=sender,
                idempotency_key="notification-test-0002",
            )

        notification = TechnicalDocumentNotification.objects.get(document=self.document)
        self.assertEqual(notification.status, TechnicalDocumentNotification.STATUS_FAILED)
        self.assertLessEqual(len(notification.error_message), MAX_AUDIT_ERROR_LENGTH)
        self.assertNotIn("super-secret", notification.error_message)
        self.assertNotIn("top-secret", notification.error_message)
        self.assertNotIn("10.0.0.8", notification.error_message)
        self.assertNotIn("/private/tmp", notification.error_message)
        self.assertNotIn("sender@example.com", notification.error_message)
        self.assertIn("[REDACTED]", notification.error_message)

    def test_same_idempotency_key_returns_existing_result_without_resending(self):
        sender = RecordingSender()
        arguments = {
            "document": self.document,
            "actor": self.actor,
            "sender": sender,
            "idempotency_key": "notification-test-0003",
            "message": "Tek sefer gönder.",
        }

        first = send_document_notification(**arguments)
        second = send_document_notification(**arguments)

        self.assertEqual(len(sender.calls), 1)
        self.assertFalse(first.deduplicated)
        self.assertTrue(second.deduplicated)
        self.assertEqual(first.notification.pk, second.notification.pk)

    def test_in_progress_key_does_not_trigger_a_second_delivery(self):
        sender = RecordingSender()
        TechnicalDocumentNotification.objects.create(
            document=self.document,
            subject="Konu",
            message="İçerik",
            recipients=["ada@example.com"],
            recipient_count=1,
            status=TechnicalDocumentNotification.STATUS_PENDING,
            sent_by=self.actor,
            idempotency_key="notification-test-0004",
        )

        with self.assertRaises(NotificationInProgress):
            send_document_notification(
                document=self.document,
                actor=self.actor,
                sender=sender,
                idempotency_key="notification-test-0004",
                subject="Konu",
                message="İçerik",
            )

        self.assertEqual(sender.calls, [])

    @override_settings(TECHNICAL_NOTIFICATION_PENDING_TIMEOUT=60)
    def test_stale_pending_key_becomes_unknown_without_replaying_smtp(self):
        sender = RecordingSender()
        notification = TechnicalDocumentNotification.objects.create(
            document=self.document,
            subject="Konu",
            message="İçerik",
            recipients=["ada@example.com"],
            recipient_count=1,
            status=TechnicalDocumentNotification.STATUS_PENDING,
            sent_by=self.actor,
            idempotency_key="notification-test-stale",
        )
        TechnicalDocumentNotification.objects.filter(pk=notification.pk).update(
            created_at=timezone.now() - timedelta(minutes=2)
        )

        with self.assertRaises(NotificationOutcomeUnknown) as raised:
            send_document_notification(
                document=self.document,
                actor=self.actor,
                sender=sender,
                idempotency_key="notification-test-stale",
                subject="Konu",
                message="İçerik",
            )

        self.assertEqual(
            raised.exception.notification.status,
            TechnicalDocumentNotification.STATUS_UNKNOWN,
        )
        self.assertEqual(sender.calls, [])

    def test_key_reuse_with_different_payload_is_rejected(self):
        sender = RecordingSender()
        send_document_notification(
            document=self.document,
            actor=self.actor,
            sender=sender,
            idempotency_key="notification-test-0005",
            message="İlk içerik",
        )

        with self.assertRaises(NotificationKeyConflict):
            send_document_notification(
                document=self.document,
                actor=self.actor,
                sender=sender,
                idempotency_key="notification-test-0005",
                message="Farklı içerik",
            )

        self.assertEqual(len(sender.calls), 1)
