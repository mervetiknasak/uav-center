from io import BytesIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .edk.models import EDKApplication
from .edk.roles import EDK_ROLE_GROUPS


class EDKApplicationApiTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.applicant = user_model.objects.create_user(
            username="edk-applicant",
            password="StrongPass123!",
        )
        self.other_applicant = user_model.objects.create_user(
            username="other-applicant",
            password="StrongPass123!",
        )
        self.approver = user_model.objects.create_user(
            username="edk-approver",
            password="StrongPass123!",
        )
        self.unassigned = user_model.objects.create_user(
            username="unassigned",
            password="StrongPass123!",
        )
        self.admin = user_model.objects.create_user(
            username="admin",
            password="StrongPass123!",
            is_staff=True,
        )
        applicant_group = Group.objects.get(name=EDK_ROLE_GROUPS["applicant"])
        approver_group = Group.objects.get(name=EDK_ROLE_GROUPS["approver"])
        applicant_group.user_set.add(self.applicant, self.other_applicant)
        approver_group.user_set.add(self.approver)
        self.payload = {
            "meeting_title": "Uçuş hazırlık değerlendirmesi",
            "project_name": "UAV Merkezi",
            "requested_date": "2026-09-10",
            "location": "Hangar toplantı odası",
            "participants": "Uçuş ekibi, kalite temsilcisi",
            "purpose": "Uçuş öncesi uygunluk kararını hazırlamak",
            "agenda": "Riskler, aksiyonlar ve sorumlular",
        }

    def create_application(self, *, applicant=None, status=EDKApplication.STATUS_PENDING):
        return EDKApplication.objects.create(
            applicant=applicant or self.applicant,
            status=status,
            **self.payload,
        )

    @staticmethod
    def word_file():
        from docx import Document

        document = Document()
        document.add_table(rows=2, cols=2)
        content = BytesIO()
        document.save(content)
        return SimpleUploadedFile(
            "edk-tutanak.docx",
            content.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    def test_applicant_creates_pending_application_and_only_sees_own_records(self):
        foreign = self.create_application(applicant=self.other_applicant)
        self.client.force_login(self.applicant)

        created = self.client.post(
            reverse("edk-application-list"),
            data={**self.payload, "status": "approved"},
            content_type="application/json",
        )
        listed = self.client.get(reverse("edk-application-list"))

        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.json()["status"], "pending")
        self.assertEqual(created.json()["applicant_name"], self.applicant.username)
        self.assertNotIn(foreign.id, [item["id"] for item in listed.json()])

    def test_user_without_role_cannot_create_application(self):
        self.client.force_login(self.unassigned)

        response = self.client.post(
            reverse("edk-application-list"),
            data=self.payload,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(EDKApplication.objects.exists())

    def test_applicant_can_open_own_application_detail_but_not_another_applicants(self):
        own_application = self.create_application(status=EDKApplication.STATUS_APPROVED)
        foreign_application = self.create_application(applicant=self.other_applicant)
        self.client.force_login(self.applicant)

        own_response = self.client.get(
            reverse("edk-application-detail", kwargs={"application_id": own_application.id})
        )
        foreign_response = self.client.get(
            reverse("edk-application-detail", kwargs={"application_id": foreign_application.id})
        )

        self.assertEqual(own_response.status_code, 200)
        self.assertTrue(own_response.json()["can_upload_minutes"])
        self.assertEqual(foreign_response.status_code, 404)

    def test_approver_can_open_any_application_detail_without_upload_permission(self):
        application = self.create_application(status=EDKApplication.STATUS_APPROVED)
        self.client.force_login(self.approver)

        response = self.client.get(
            reverse("edk-application-detail", kwargs={"application_id": application.id})
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], application.id)
        self.assertFalse(response.json()["can_upload_minutes"])

    def test_removed_legacy_word_to_jira_route_returns_not_found(self):
        self.client.force_login(self.applicant)

        response = self.client.post("/api/word-to-jira/parse/")

        self.assertEqual(response.status_code, 404)

    def test_application_rejects_blank_and_oversized_form_values(self):
        self.client.force_login(self.applicant)

        response = self.client.post(
            reverse("edk-application-list"),
            data={**self.payload, "purpose": " ", "participants": "A" * 2001},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("purpose", response.json())
        self.assertIn("participants", response.json())

    def test_approver_sees_all_applications_and_can_approve(self):
        application = self.create_application()
        self.create_application(applicant=self.other_applicant)
        self.client.force_login(self.approver)

        listed = self.client.get(reverse("edk-application-list"))
        approved = self.client.post(
            reverse("edk-application-decision", kwargs={"application_id": application.id}),
            data={"status": "approved", "decision_note": "Uygundur."},
            content_type="application/json",
        )

        self.assertEqual(len(listed.json()), 2)
        self.assertEqual(approved.status_code, 200)
        self.assertEqual(approved.json()["status"], "approved")
        self.assertEqual(approved.json()["reviewed_by_name"], self.approver.username)

    def test_rejection_requires_reason_and_terminal_decision_returns_conflict(self):
        application = self.create_application()
        self.client.force_login(self.approver)
        url = reverse(
            "edk-application-decision",
            kwargs={"application_id": application.id},
        )

        missing_reason = self.client.post(
            url,
            data={"status": "rejected", "decision_note": ""},
            content_type="application/json",
        )
        self.client.post(
            url,
            data={"status": "approved"},
            content_type="application/json",
        )
        second_decision = self.client.post(
            url,
            data={"status": "rejected", "decision_note": "Geç kaldı."},
            content_type="application/json",
        )

        self.assertEqual(missing_reason.status_code, 400)
        self.assertIn("decision_note", missing_reason.json())
        self.assertEqual(second_decision.status_code, 409)

    def test_approver_cannot_decide_own_application(self):
        applicant_group = Group.objects.get(name=EDK_ROLE_GROUPS["applicant"])
        applicant_group.user_set.add(self.approver)
        application = self.create_application(applicant=self.approver)
        self.client.force_login(self.approver)

        response = self.client.post(
            reverse("edk-application-decision", kwargs={"application_id": application.id}),
            data={"status": "approved"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 409)
        application.refresh_from_db()
        self.assertEqual(application.status, EDKApplication.STATUS_PENDING)

    @patch("api.edk.views.parse_minutes_document")
    def test_minutes_upload_opens_only_after_approval_and_records_upload(self, parser):
        parser.return_value = {
            "table_count": 1,
            "cell_count": 1,
            "cells": [
                {"index": 0, "table_index": 0, "row_index": 0, "column_index": 0, "text": "EDK"}
            ],
            "extracted_data": {
                "project": "UAV",
                "subject": "EDK",
                "mom_no": "EDK-1",
                "revision": "A",
                "date_time": "",
                "location": "",
                "agenda": "",
                "discussions_decisions": "",
                "action_items": [],
            },
        }
        application = self.create_application()
        self.client.force_login(self.applicant)
        url = reverse("edk-minutes-parse", kwargs={"application_id": application.id})

        blocked = self.client.post(url, data={"file": self.word_file()})
        application.status = EDKApplication.STATUS_APPROVED
        application.reviewed_by = self.approver
        application.reviewed_at = timezone.now()
        application.save(update_fields=["status", "reviewed_by", "reviewed_at"])
        uploaded = self.client.post(url, data={"file": self.word_file()})

        self.assertEqual(blocked.status_code, 409)
        self.assertEqual(uploaded.status_code, 200)
        application.refresh_from_db()
        self.assertEqual(application.minutes_file_name, "edk-tutanak.docx")
        self.assertIsNotNone(application.minutes_uploaded_at)

    def test_other_applicant_cannot_discover_or_upload_to_application(self):
        application = self.create_application(status=EDKApplication.STATUS_APPROVED)
        self.client.force_login(self.other_applicant)

        response = self.client.post(
            reverse("edk-minutes-parse", kwargs={"application_id": application.id}),
            data={"file": self.word_file()},
        )

        self.assertEqual(response.status_code, 404)

    def test_admin_can_assign_edk_roles(self):
        self.client.force_login(self.admin)

        response = self.client.patch(
            reverse("admin-user-edk-roles", kwargs={"user_id": self.unassigned.id}),
            data={"edk_roles": ["applicant", "approver"]},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.json()["edk_roles"]), {"applicant", "approver"})
