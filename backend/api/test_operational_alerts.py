import json
from datetime import datetime, time, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from .form_processes.models import FormProcessRecord
from .operational_alerts.services import _flight_permit_alert, build_operational_alerts
from .organization.models import PanelResponsible, Project, ProjectPanel
from .technical_documents.models import (
    TechnicalDocument,
    TechnicalDocumentStatusHistory,
)


@override_settings(TIME_ZONE="Europe/Istanbul", USE_TZ=True)
class OperationalAlertApiTests(APITestCase):
    AS_OF = datetime(2026, 8, 20).date()

    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="alert-reader", password="pass")
        self.admin = user_model.objects.create_user(
            username="alert-admin",
            password="pass",
            is_staff=True,
        )
        self.project = Project.objects.create(name="ANKA III", code="ANKA3")
        self.panel = ProjectPanel.objects.create(project=self.project, name="Uçuş Bilimleri")

    def create_document(self, code, **overrides):
        values = {
            "project": self.project,
            "code": code,
            "title": f"{code} başlığı",
            "status": TechnicalDocument.STATUS_DRAFT,
        }
        values.update(overrides)
        document = TechnicalDocument.objects.create(**values)
        document.panels.add(self.panel)
        return document

    def create_status_history(self, document, *, to_status, days_ago):
        history = TechnicalDocumentStatusHistory.objects.create(
            document=document,
            to_status=to_status,
        )
        local_timestamp = datetime.combine(
            self.AS_OF - timedelta(days=days_ago),
            time(hour=12),
        )
        TechnicalDocumentStatusHistory.objects.filter(pk=history.pk).update(
            created_at=timezone.make_aware(local_timestamp),
        )
        return history

    def create_flight_permit(
        self,
        number,
        *,
        days_remaining,
        lifecycle_status="approved",
        record_status=FormProcessRecord.STATUS_APPROVED,
    ):
        return FormProcessRecord.objects.create(
            process_code="flight-permits",
            template_code="fm_qua_0579",
            record_number=number,
            title=f"{number} uçuş izni",
            status=record_status,
            data={
                "permit_lifecycle_status": lifecycle_status,
                "valid_until": (self.AS_OF + timedelta(days=days_remaining)).isoformat(),
            },
        )

    def get_alerts(self):
        with patch("api.operational_alerts.views.timezone") as mocked_timezone:
            mocked_timezone.localdate.return_value = self.AS_OF
            return self.client.get(reverse("operational-alert-list"))

    def test_due_date_boundaries_are_inclusive_and_summary_counts_alerts(self):
        for days_remaining in (-1, 0, 7, 8, 30, 31):
            self.create_document(
                f"DUE-{days_remaining}",
                due_date=self.AS_OF + timedelta(days=days_remaining),
            )
        self.client.force_authenticate(self.user)

        response = self.get_alerts()

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["as_of"], "2026-08-20")
        self.assertEqual(
            payload["thresholds"],
            {"critical_days": 7, "horizon_days": 30, "stale_days": 14},
        )
        self.assertEqual(
            payload["summary"],
            {
                "total": 5,
                "overdue": 1,
                "next_7_days": 2,
                "next_30_days": 2,
                "stale": 0,
            },
        )
        by_remaining = {alert["days_remaining"]: alert for alert in payload["alerts"]}
        self.assertEqual(by_remaining[-1]["bucket"], "overdue")
        self.assertEqual(by_remaining[0]["bucket"], "next_7_days")
        self.assertEqual(by_remaining[7]["bucket"], "next_7_days")
        self.assertEqual(by_remaining[8]["bucket"], "next_30_days")
        self.assertEqual(by_remaining[30]["bucket"], "next_30_days")
        self.assertNotIn(31, by_remaining)

    def test_document_rules_allow_distinct_alerts_and_apply_terminal_statuses(self):
        active = self.create_document(
            "MULTI",
            due_date=self.AS_OF - timedelta(days=1),
            review_date=self.AS_OF + timedelta(days=5),
        )
        published = self.create_document(
            "PUBLISHED",
            status=TechnicalDocument.STATUS_PUBLISHED,
            due_date=self.AS_OF - timedelta(days=2),
            review_date=self.AS_OF + timedelta(days=3),
        )
        for status_value in (
            TechnicalDocument.STATUS_SUPERSEDED,
            TechnicalDocument.STATUS_ARCHIVED,
        ):
            self.create_document(
                status_value.upper(),
                status=status_value,
                due_date=self.AS_OF - timedelta(days=3),
                review_date=self.AS_OF + timedelta(days=4),
            )
        self.client.force_authenticate(self.user)

        response = self.get_alerts()

        self.assertEqual(response.status_code, 200)
        alerts = response.json()["alerts"]
        self.assertEqual(
            {alert["key"] for alert in alerts},
            {
                f"technical_document:{active.pk}:due_date",
                f"technical_document:{active.pk}:review_date",
                f"technical_document:{published.pk}:review_date",
            },
        )

    def test_review_dates_and_flight_permits_share_the_date_boundary_contract(self):
        expected_buckets = {
            -1: "overdue",
            0: "next_7_days",
            7: "next_7_days",
            8: "next_30_days",
            30: "next_30_days",
        }
        for days_remaining in (*expected_buckets, 31):
            self.create_document(
                f"REVIEW-{days_remaining}",
                status=TechnicalDocument.STATUS_PUBLISHED,
                review_date=self.AS_OF + timedelta(days=days_remaining),
            )
            self.create_flight_permit(
                f"FP-{days_remaining}",
                days_remaining=days_remaining,
            )
        self.client.force_authenticate(self.user)

        response = self.get_alerts()

        self.assertEqual(response.status_code, 200)
        alerts = response.json()["alerts"]
        for alert_type in ("review_date", "valid_until"):
            buckets = {
                alert["days_remaining"]: alert["bucket"]
                for alert in alerts
                if alert["alert_type"] == alert_type
            }
            self.assertEqual(buckets, expected_buckets)

    def test_workflow_stale_uses_latest_transition_into_current_status(self):
        stale = self.create_document(
            "STALE-14",
            status=TechnicalDocument.STATUS_CHANGES_REQUESTED,
        )
        self.create_status_history(
            stale,
            to_status=TechnicalDocument.STATUS_CHANGES_REQUESTED,
            days_ago=14,
        )
        recent = self.create_document(
            "RECENT-CURRENT",
            status=TechnicalDocument.STATUS_IN_REVIEW,
        )
        self.create_status_history(
            recent,
            to_status=TechnicalDocument.STATUS_IN_REVIEW,
            days_ago=40,
        )
        self.create_status_history(
            recent,
            to_status=TechnicalDocument.STATUS_IN_REVIEW,
            days_ago=13,
        )
        self.create_document(
            "NO-HISTORY",
            status=TechnicalDocument.STATUS_IN_REVIEW,
        )
        self.client.force_authenticate(self.user)

        response = self.get_alerts()

        self.assertEqual(response.status_code, 200)
        alerts = response.json()["alerts"]
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["key"], f"technical_document:{stale.pk}:workflow_stale")
        self.assertEqual(alerts[0]["date"], "2026-08-06")
        self.assertIsNone(alerts[0]["days_remaining"])
        self.assertEqual(alerts[0]["days_in_status"], 14)
        self.assertEqual(alerts[0]["bucket"], "stale")

    def test_only_approved_flight_permits_inside_horizon_are_returned(self):
        overdue = self.create_flight_permit("FP-OVERDUE", days_remaining=-1)
        horizon = self.create_flight_permit("FP-HORIZON", days_remaining=30)
        self.create_flight_permit("FP-OUTSIDE", days_remaining=31)
        for lifecycle_status in ("draft", "suspended", "revoked"):
            self.create_flight_permit(
                f"FP-{lifecycle_status.upper()}",
                days_remaining=5,
                lifecycle_status=lifecycle_status,
            )
        for record_status in (
            FormProcessRecord.STATUS_DRAFT,
            FormProcessRecord.STATUS_IN_REVIEW,
            FormProcessRecord.STATUS_ARCHIVED,
        ):
            self.create_flight_permit(
                f"FP-RECORD-{record_status.upper()}",
                days_remaining=5,
                record_status=record_status,
            )
        FormProcessRecord.objects.create(
            process_code="flight-permits",
            template_code="fm_qua_0579",
            record_number="FP-INVALID-DATE",
            title="Geçersiz tarihli uçuş izni",
            status=FormProcessRecord.STATUS_APPROVED,
            data={"permit_lifecycle_status": "approved", "valid_until": "not-a-date"},
        )
        self.client.force_authenticate(self.user)

        response = self.get_alerts()

        self.assertEqual(response.status_code, 200)
        alerts = response.json()["alerts"]
        self.assertEqual(
            {alert["key"] for alert in alerts},
            {
                f"flight_permit:{overdue.pk}:valid_until",
                f"flight_permit:{horizon.pk}:valid_until",
            },
        )
        self.assertTrue(all(alert["source_type"] == "flight_permit" for alert in alerts))
        self.assertTrue(all(alert["status"] == "approved" for alert in alerts))
        self.assertTrue(all(alert["can_notify"] is False for alert in alerts))

    def test_malformed_flight_permit_data_is_ignored_safely(self):
        record = self.create_flight_permit("FP-MALFORMED", days_remaining=1)
        for invalid_data in (None, [], "approved"):
            record.data = invalid_data
            with self.subTest(data=invalid_data):
                self.assertIsNone(_flight_permit_alert(record, as_of=self.AS_OF))

    def test_endpoint_requires_active_user_and_only_exposes_notify_capability(self):
        document = self.create_document("SECURITY", due_date=self.AS_OF)
        PanelResponsible.objects.create(
            panel=self.panel,
            name="Gizli Alıcı",
            email="recipient@example.com",
        )

        self.assertEqual(self.get_alerts().status_code, 403)

        inactive = get_user_model().objects.create_user(
            username="inactive-alert-reader",
            password="pass",
            is_active=False,
        )
        self.client.force_authenticate(inactive)
        self.assertEqual(self.get_alerts().status_code, 403)

        self.client.force_authenticate(self.user)
        reader_payload = self.get_alerts().json()
        reader_alert = reader_payload["alerts"][0]
        self.assertEqual(reader_alert["source_id"], document.pk)
        self.assertFalse(reader_alert["can_notify"])
        serialized_payload = json.dumps(reader_payload)
        self.assertNotIn("recipient@example.com", serialized_payload)
        self.assertNotIn("recipients", serialized_payload)

        self.client.force_authenticate(self.admin)
        admin_alert = self.get_alerts().json()["alerts"][0]
        self.assertTrue(admin_alert["can_notify"])

    def test_response_shape_sorting_and_prefetch_are_stable(self):
        older_overdue = self.create_document(
            "Z-OVERDUE",
            due_date=self.AS_OF - timedelta(days=10),
        )
        later_overdue = self.create_document(
            "A-OVERDUE",
            due_date=self.AS_OF - timedelta(days=2),
        )
        next_7_days = self.create_document(
            "NEXT-7",
            due_date=self.AS_OF + timedelta(days=7),
        )
        next_30_days = self.create_document(
            "NEXT-30",
            due_date=self.AS_OF + timedelta(days=30),
        )
        stale = self.create_document(
            "STALE-SORT",
            status=TechnicalDocument.STATUS_IN_REVIEW,
        )
        self.create_status_history(
            stale,
            to_status=TechnicalDocument.STATUS_IN_REVIEW,
            days_ago=20,
        )

        with self.assertNumQueries(3):
            payload = build_operational_alerts(as_of=self.AS_OF, is_staff=True)

        self.assertEqual(
            [alert["source_id"] for alert in payload["alerts"]],
            [
                older_overdue.pk,
                later_overdue.pk,
                next_7_days.pk,
                next_30_days.pk,
                stale.pk,
            ],
        )
        self.assertEqual(
            set(payload["alerts"][0]),
            {
                "key",
                "source_type",
                "source_id",
                "alert_type",
                "bucket",
                "date",
                "days_remaining",
                "days_in_status",
                "reference",
                "title",
                "status",
                "status_display",
                "priority",
                "project",
                "panels",
                "can_notify",
            },
        )
