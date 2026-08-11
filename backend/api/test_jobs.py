import importlib
from datetime import timedelta
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .documents.services.lifecycle import delete_document
from .models import AsyncJob, Document
from .services.job_queue import (
    MAX_JOB_ERROR_LENGTH,
    claim_next_job,
    enqueue_document_processing,
    execute_job,
    fail_or_retry_job,
    recover_stale_jobs,
)


class AsyncJobApiTests(TestCase):
    def setUp(self):
        self.media_directory = TemporaryDirectory()
        self.settings_override = override_settings(MEDIA_ROOT=self.media_directory.name)
        self.settings_override.enable()
        users = get_user_model().objects
        self.user = users.create_user(username="job-owner", password="StrongPass123!")
        self.other_user = users.create_user(username="other-owner", password="StrongPass123!")
        self.client.force_login(self.user)

    def tearDown(self):
        self.settings_override.disable()
        self.media_directory.cleanup()

    def create_job(self, owner=None, name="requirements.txt"):
        owner = owner or self.user
        document = Document.objects.create(
            original_name=name,
            file=SimpleUploadedFile(name, b"REQ-1 shall fly", content_type="text/plain"),
            content_type="text/plain",
            size=16,
            prompt="Özetle",
        )
        return enqueue_document_processing(
            document=document,
            owner=owner,
            use_ocr=False,
            use_ai=False,
        )

    def test_upload_returns_accepted_job_without_running_work_in_request(self):
        with patch("api.services.job_queue.extract_document") as mocked_extract:
            response = self.client.post(
                reverse("document-upload"),
                data={
                    "file": SimpleUploadedFile("not.txt", b"metin", content_type="text/plain"),
                    "prompt": "",
                    "use_ai": "false",
                },
            )

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.json()["job"]["status"], AsyncJob.STATUS_QUEUED)
        self.assertEqual(response.json()["document"]["status"], Document.STATUS_PENDING)
        self.assertEqual(AsyncJob.objects.get().owner, self.user)
        self.assertEqual(Document.objects.get().owner, self.user)
        mocked_extract.assert_not_called()

    def test_ingestion_failure_rolls_back_records_and_removes_stored_upload(self):
        from api.documents.services.ingestion import ingest_document

        def fail_enqueue(**_kwargs):
            raise RuntimeError("queue unavailable")

        with self.assertRaisesMessage(RuntimeError, "queue unavailable"):
            ingest_document(
                upload=SimpleUploadedFile(
                    "rollback.txt",
                    b"temporary content",
                    content_type="text/plain",
                ),
                prompt="",
                use_ocr=False,
                use_ai=False,
                owner=self.user,
                enqueue=fail_enqueue,
            )

        self.assertFalse(Document.objects.exists())
        self.assertFalse(AsyncJob.objects.exists())
        self.assertEqual(list(Path(self.media_directory.name).rglob("rollback.txt")), [])

    def test_deleting_owner_retains_document_for_staff_audit(self):
        retained_document = Document.objects.create(
            original_name="retained.txt",
            file=SimpleUploadedFile("retained.txt", b"audit evidence"),
            owner=self.user,
        )

        self.user.delete()

        retained_document.refresh_from_db()
        self.assertIsNone(retained_document.owner)

    def test_document_delete_removes_file_only_after_database_commit(self):
        document = Document.objects.create(
            original_name="delete-after-commit.txt",
            file=SimpleUploadedFile("delete-after-commit.txt", b"temporary"),
            owner=self.user,
        )
        stored_path = Path(document.file.path)

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.delete(
                reverse("document-detail", kwargs={"document_id": document.pk})
            )

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Document.objects.filter(pk=document.pk).exists())
        self.assertFalse(stored_path.exists())

    def test_document_delete_rollback_keeps_database_row_and_file(self):
        document = Document.objects.create(
            original_name="rollback-delete.txt",
            file=SimpleUploadedFile("rollback-delete.txt", b"audit evidence"),
            owner=self.user,
        )
        document_id = document.pk
        stored_path = Path(document.file.path)
        original_delete = Document.delete

        def delete_then_fail(instance, *args, **kwargs):
            original_delete(instance, *args, **kwargs)
            raise RuntimeError("database delete failed")

        with (
            patch.object(Document, "delete", new=delete_then_fail),
            self.assertRaisesMessage(RuntimeError, "database delete failed"),
        ):
            delete_document(document=document)

        self.assertTrue(Document.objects.filter(pk=document_id).exists())
        self.assertTrue(stored_path.exists())

    def test_user_only_lists_and_opens_own_jobs(self):
        own_job = self.create_job()
        other_job = self.create_job(owner=self.other_user, name="secret.txt")

        response = self.client.get(reverse("job-list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in response.json()], [str(own_job.id)])
        self.assertEqual(
            self.client.get(reverse("job-detail", kwargs={"job_id": other_job.id})).status_code,
            404,
        )

    def test_user_can_cancel_only_own_queued_job(self):
        own_job = self.create_job()
        other_job = self.create_job(owner=self.other_user, name="other.txt")

        response = self.client.post(reverse("job-cancel", kwargs={"job_id": own_job.id}))

        self.assertEqual(response.status_code, 200)
        own_job.refresh_from_db()
        self.assertEqual(own_job.status, AsyncJob.STATUS_CANCELLED)
        self.assertEqual(
            self.client.post(reverse("job-cancel", kwargs={"job_id": other_job.id})).status_code,
            404,
        )

    @override_settings(JOB_RETRY_BASE_SECONDS=10)
    def test_failure_requeues_with_exponential_backoff_before_attempt_limit(self):
        job = self.create_job()
        now = timezone.now()
        AsyncJob.objects.filter(pk=job.pk).update(
            status=AsyncJob.STATUS_RUNNING,
            attempts=2,
            max_attempts=3,
        )
        job.refresh_from_db()

        with patch("api.services.job_queue.timezone.now", return_value=now):
            result = fail_or_retry_job(job, RuntimeError("temporary outage"))

        job.refresh_from_db()
        self.assertEqual(result, AsyncJob.STATUS_QUEUED)
        self.assertEqual(job.status, AsyncJob.STATUS_QUEUED)
        self.assertEqual(job.available_at, now + timedelta(seconds=20))
        self.assertIsNone(job.locked_at)

    def test_terminal_failure_marks_job_and_document_with_safe_bounded_error(self):
        job = self.create_job()
        AsyncJob.objects.filter(pk=job.pk).update(
            status=AsyncJob.STATUS_RUNNING,
            attempts=3,
            max_attempts=3,
        )
        job.refresh_from_db()

        result = fail_or_retry_job(
            job,
            RuntimeError(
                "password=super-secret token=top-secret "
                "http://10.0.0.8:11434/private "
                "/Users/operator/private.txt "
                r"C:\Users\Operator\private.txt "
                "pilot@example.com " + ("x" * 2000)
            ),
        )

        job.refresh_from_db()
        job.document.refresh_from_db()
        self.assertEqual(result, AsyncJob.STATUS_FAILED)
        self.assertEqual(job.status, AsyncJob.STATUS_FAILED)
        self.assertEqual(job.document.status, Document.STATUS_FAILED)
        self.assertLessEqual(len(job.error_message), MAX_JOB_ERROR_LENGTH)
        self.assertLessEqual(len(job.document.error_message), MAX_JOB_ERROR_LENGTH)
        self.assertNotIn("super-secret", job.error_message)
        self.assertNotIn("top-secret", job.error_message)
        self.assertNotIn("10.0.0.8", job.error_message)
        self.assertNotIn("/Users/operator", job.error_message)
        self.assertNotIn(r"C:\Users\Operator", job.error_message)
        self.assertNotIn("pilot@example.com", job.error_message)
        self.assertIn("[REDACTED]", job.error_message)

    def test_worker_stderr_uses_safe_exception_message(self):
        from django.core.management import call_command

        fake_job = SimpleNamespace(id="job-1", job_type="document_processing", attempts=1)
        stderr = StringIO()
        unsafe_error = RuntimeError(
            "token=worker-secret http://10.0.0.9:11434/api "
            "/private/tmp/secret.docx worker@example.com"
        )

        with (
            patch("api.management.commands.run_job_worker.recover_stale_jobs"),
            patch(
                "api.management.commands.run_job_worker.claim_next_job",
                return_value=fake_job,
            ),
            patch(
                "api.management.commands.run_job_worker.execute_job",
                side_effect=unsafe_error,
            ),
            patch(
                "api.management.commands.run_job_worker.fail_or_retry_job",
                return_value=AsyncJob.STATUS_QUEUED,
            ),
        ):
            call_command(
                "run_job_worker",
                once=True,
                worker_id="test-worker",
                stdout=StringIO(),
                stderr=stderr,
            )

        output = stderr.getvalue()
        self.assertIn("job-1", output)
        self.assertNotIn("worker-secret", output)
        self.assertNotIn("10.0.0.9", output)
        self.assertNotIn("/private/tmp", output)
        self.assertNotIn("worker@example.com", output)

    @override_settings(JOB_STALE_TIMEOUT=60)
    def test_stale_recovery_requeues_retryable_and_fails_exhausted_jobs(self):
        retryable = self.create_job(name="retryable.txt")
        exhausted = self.create_job(name="exhausted.txt")
        stale_time = timezone.now() - timedelta(minutes=5)
        AsyncJob.objects.filter(pk=retryable.pk).update(
            status=AsyncJob.STATUS_RUNNING,
            attempts=1,
            max_attempts=3,
            locked_at=stale_time,
        )
        AsyncJob.objects.filter(pk=exhausted.pk).update(
            status=AsyncJob.STATUS_RUNNING,
            attempts=3,
            max_attempts=3,
            locked_at=stale_time,
        )

        recovered_count = recover_stale_jobs()

        retryable.refresh_from_db()
        exhausted.refresh_from_db()
        exhausted.document.refresh_from_db()
        self.assertEqual(recovered_count, 2)
        self.assertEqual(retryable.status, AsyncJob.STATUS_QUEUED)
        self.assertEqual(retryable.progress, 0)
        self.assertEqual(exhausted.status, AsyncJob.STATUS_FAILED)
        self.assertEqual(exhausted.document.status, Document.STATUS_FAILED)

    def test_owner_migration_backfills_only_unambiguous_job_owners(self):
        migration = importlib.import_module("api.migrations.0013_document_owner")
        unambiguous = Document.objects.create(
            original_name="unambiguous.txt",
            file="documents/unambiguous.txt",
        )
        ambiguous = Document.objects.create(
            original_name="ambiguous.txt",
            file="documents/ambiguous.txt",
        )
        AsyncJob.objects.create(
            owner=self.user,
            job_type=AsyncJob.TYPE_DOCUMENT_PROCESSING,
            document=unambiguous,
        )
        AsyncJob.objects.create(
            owner=self.user,
            job_type=AsyncJob.TYPE_DOCUMENT_PROCESSING,
            document=ambiguous,
        )
        AsyncJob.objects.create(
            owner=self.other_user,
            job_type=AsyncJob.TYPE_DOCUMENT_PROCESSING,
            document=ambiguous,
        )

        migration.backfill_document_owners(
            apps,
            SimpleNamespace(connection=connection),
        )

        unambiguous.refresh_from_db()
        ambiguous.refresh_from_db()
        self.assertEqual(unambiguous.owner, self.user)
        self.assertIsNone(ambiguous.owner)

    @patch("api.services.job_queue.index_document", return_value=1)
    @patch("api.services.job_queue.extract_document")
    def test_worker_claims_and_completes_document_job(self, mocked_extract, _mocked_index):
        mocked_extract.return_value = {
            "text": "REQ-1 shall fly",
            "ocr": {
                "enabled": False,
                "engine": None,
                "languages": [],
                "processed_images": 0,
                "processed_pages": 0,
                "email_addresses": [],
                "warnings": [],
            },
        }
        queued_job = self.create_job()

        claimed_job = claim_next_job("test-worker")
        execute_job(claimed_job)

        queued_job.refresh_from_db()
        queued_job.document.refresh_from_db()
        self.assertEqual(queued_job.status, AsyncJob.STATUS_COMPLETED)
        self.assertEqual(queued_job.progress, 100)
        self.assertEqual(queued_job.document.status, Document.STATUS_PROCESSED)
        self.assertEqual(queued_job.document.extracted_text, "REQ-1 shall fly")
