from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import AsyncJob, Document
from .services.job_queue import claim_next_job, enqueue_document_processing, execute_job


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
        document = Document.objects.create(
            original_name=name,
            file=SimpleUploadedFile(name, b"REQ-1 shall fly", content_type="text/plain"),
            content_type="text/plain",
            size=16,
            prompt="Özetle",
        )
        return enqueue_document_processing(
            document=document,
            owner=owner or self.user,
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
        mocked_extract.assert_not_called()

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
