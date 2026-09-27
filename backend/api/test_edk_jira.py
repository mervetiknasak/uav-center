from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase, override_settings
from django.urls import reverse

from .edk.jira import build_jira_draft, fetch_jira_tracking, publish_jira_draft
from .edk.roles import EDK_ROLE_GROUPS
from .edk.services import EDKJiraConflict, link_edk_jira_issue
from .models import (
    EDKApplication,
    PanelResponsible,
    Person,
    PersonGroup,
    Project,
    ProjectPanel,
)
from .services.jira_connector import JiraConnectorError


@override_settings(
    JIRA_SERVER="http://jira.local",
    JIRA_PERSONAL_ACCESS_TOKEN="test-token",
)
class EDKJiraTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="jira-user",
            password="StrongPass123!",
        )
        self.admin = get_user_model().objects.create_user(
            username="jira-admin",
            password="StrongPass123!",
            is_staff=True,
        )
        project = Project.objects.create(name="İHA", code="UAV")
        panel = ProjectPanel.objects.create(project=project, name="Uçuş")
        PanelResponsible.objects.create(
            panel=panel,
            name="Ada",
            username="ada.local",
        )
        self.application = EDKApplication.objects.create(
            applicant=self.user,
            aircraft_name="Hürkuş",
            project=project,
            status=EDKApplication.STATUS_APPROVED,
            minutes_file_name="edk-tutanak.docx",
        )
        Group.objects.get(name=EDK_ROLE_GROUPS["applicant"]).user_set.add(self.user)
        self.extracted = {
            "project": "UAV",
            "subject": "Uçuş hazırlığı",
            "mom_no": "MOM-42",
            "revision": "B",
            "date_time": "2026-07-01 10:00",
            "location": "Hangar",
            "agenda": "Hazırlık",
            "discussions_decisions": "Kontroller tamamlanacak.",
            "action_items": [
                {
                    "no": "1",
                    "action_item": "Motor kontrolünü tamamla",
                    "responsible": "Ada",
                    "due_date": "2026-07-10",
                }
            ],
        }

    def test_builds_parent_and_username_mapped_subtask_draft(self):
        draft = build_jira_draft(self.extracted)

        self.assertEqual(draft["task"]["project_key"], "MOM")
        self.assertEqual(draft["task"]["summary"], "Uçuş hazırlığı")
        self.assertEqual(len(draft["task"]["meeting_fields"]), 8)
        self.assertEqual(draft["subtasks"][0]["username"], "ada.local")

    def test_matches_action_responsibles_from_every_registered_person_source(self):
        application_member = get_user_model().objects.create_user(
            username="selin.jira",
            first_name="Selin",
            last_name="Arslan",
        )
        group = PersonGroup.objects.create(name="Uçuş Emniyeti")
        group_person = Person.objects.create(name="Mert Kaya", username="mert.jira")
        group.people.add(group_person)
        extracted = {
            **self.extracted,
            "action_items": [
                {"action_item": "Üye aksiyonu", "responsible": " Selin   Arslan "},
                {"action_item": "Grup aksiyonu", "responsible": "MERT KAYA"},
                {"action_item": "Panel aksiyonu", "responsible": "Ada"},
            ],
        }

        draft = build_jira_draft(extracted)

        self.assertIsNotNone(application_member.pk)
        self.assertEqual(
            [item["username"] for item in draft["subtasks"]],
            ["selin.jira", "mert.jira", "ada.local"],
        )
        self.assertEqual(draft["warnings"], [])

    def test_does_not_assign_an_ambiguous_name_to_a_username(self):
        group = PersonGroup.objects.create(name="Aviyonik")
        group.people.add(Person.objects.create(name="Ada", username="other.ada"))

        draft = build_jira_draft(self.extracted)

        self.assertIsNone(draft["subtasks"][0]["username"])
        self.assertEqual(
            draft["warnings"],
            ["Bazı sorumlular için username eşleşmesi bulunamadı."],
        )

    def jira_payload(self):
        return {
            **build_jira_draft(self.extracted),
            "jsession": "user-session-123",
        }

    def test_publishes_parent_before_subtask(self):
        jira = Mock()
        jira.server_url = "http://jira.local"
        jira.search_issues.return_value = []
        jira.create_issue.side_effect = [Mock(key="UAV-10"), Mock(key="UAV-11")]
        draft = build_jira_draft(self.extracted)

        result = publish_jira_draft(draft, jira=jira)

        self.assertEqual(result["task"]["key"], "UAV-10")
        self.assertEqual(result["subtasks"][0]["key"], "UAV-11")
        subtask_call = jira.create_issue.call_args_list[1].kwargs
        self.assertEqual(subtask_call["parent_key"], "UAV-10")
        self.assertEqual(subtask_call["assignee_username"], "ada.local")
        self.assertEqual(subtask_call["custom_fields"], {"duedate": "2026-07-10"})

    def test_subtask_failure_exposes_only_stable_public_error(self):
        jira = Mock()
        jira.server_url = "http://jira.local"
        jira.search_issues.return_value = []
        jira.create_issue.side_effect = [
            Mock(key="UAV-10"),
            JiraConnectorError("token=secret http://jira.internal /private/cert.pem"),
        ]

        result = publish_jira_draft(
            {
                "task": {"project_key": "UAV", "summary": "Uçuş hazırlığı"},
                "subtasks": [
                    {
                        "client_id": "action-1",
                        "enabled": True,
                        "summary": "Motor kontrolü",
                    }
                ],
            },
            jira=jira,
        )

        self.assertEqual(result["subtasks"][0]["status"], "error")
        self.assertEqual(
            result["subtasks"][0]["error"],
            "Alt görev Jira'ya aktarılamadı.",
        )
        self.assertNotIn("jira.internal", str(result))

    def test_fetches_task_summary_and_detects_when_every_subtask_is_closed(self):
        jira = Mock()
        jira.server_url = "http://jira.local"
        jira.issue.return_value = self.jira_issue(
            "UAV-10",
            "Uçuş hazırlığı",
            "Devam Ediyor",
            "indeterminate",
        )
        jira.search_issues.return_value = [
            self.jira_issue("UAV-11", "Motor kontrolü", "Tamamlandı", "done"),
            self.jira_issue("UAV-12", "Uçuş kontrolü", "Kapalı", "done"),
        ]

        tracking = fetch_jira_tracking("UAV-10", jira=jira)

        self.assertEqual(tracking["summary"], "Uçuş hazırlığı")
        self.assertEqual(tracking["subtask_total"], 2)
        self.assertEqual(tracking["subtask_closed"], 2)
        self.assertTrue(tracking["all_subtasks_closed"])
        jira.search_issues.assert_called_once_with(
            'parent = "UAV-10"',
            max_results=False,
            fields=["key", "summary", "status"],
        )

    def test_tracking_with_no_subtasks_is_not_reported_as_complete(self):
        jira = Mock()
        jira.server_url = "http://jira.local"
        jira.issue.return_value = self.jira_issue("UAV-10", "EDK", "Açık", "new")
        jira.search_issues.return_value = []

        tracking = fetch_jira_tracking("UAV-10", jira=jira)

        self.assertFalse(tracking["all_subtasks_closed"])

    @patch("api.edk.views.JiraConnector")
    def test_application_publish_persists_jira_link_and_initial_tracking(self, connector):
        jira = connector.return_value
        jira.server_url = "http://jira.local"
        jira.create_issue.side_effect = [Mock(key="UAV-10"), Mock(key="UAV-11")]
        jira.issue.return_value = self.jira_issue(
            "UAV-10",
            "Uçuş hazırlığı",
            "Açık",
            "new",
        )
        jira.search_issues.side_effect = lambda jql, **_kwargs: (
            []
            if jql.startswith("project =")
            else [self.jira_issue("UAV-11", "Motor kontrolü", "Açık", "new")]
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "edk-application-jira-publish",
                kwargs={"application_id": self.application.id},
            ),
            data=self.jira_payload(),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        self.application.refresh_from_db()
        self.assertEqual(self.application.jira_issue_key, "UAV-10")
        self.assertEqual(self.application.jira_url, "http://jira.local/browse/UAV-10")
        self.assertEqual(self.application.jira_summary, "Uçuş hazırlığı")
        self.assertEqual(response.json()["tracking"]["subtask_total"], 1)
        self.assertFalse(response.json()["tracking"]["all_subtasks_closed"])
        connector.assert_called_once_with(jsession="user-session-123")

    @patch("api.edk.views.JiraConnector")
    def test_application_publish_keeps_link_when_initial_tracking_refresh_fails(self, connector):
        jira = connector.return_value
        jira.server_url = "http://jira.local"
        jira.search_issues.return_value = []
        jira.create_issue.side_effect = [Mock(key="UAV-10"), Mock(key="UAV-11")]
        jira.issue.side_effect = JiraConnectorError("Jira geçici olarak kullanılamıyor")
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse(
                "edk-application-jira-publish",
                kwargs={"application_id": self.application.id},
            ),
            data=self.jira_payload(),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        self.application.refresh_from_db()
        self.assertEqual(self.application.jira_issue_key, "UAV-10")
        self.assertIsNone(self.application.jira_last_synced_at)
        self.assertIn("daha sonra yenilenmelidir", response.json()["message"])

    @patch("api.edk.views.JiraConnector")
    def test_application_publish_hides_other_users_edk_and_requires_approved_minutes(
        self, connector
    ):
        url = reverse(
            "edk-application-jira-publish",
            kwargs={"application_id": self.application.id},
        )
        draft = self.jira_payload()
        foreign_user = get_user_model().objects.create_user(
            username="foreign-publisher",
            password="StrongPass123!",
        )
        self.client.force_login(foreign_user)
        denied = self.client.post(url, data=draft, content_type="application/json")
        self.application.minutes_file_name = ""
        self.application.save(update_fields=["minutes_file_name"])
        self.client.force_login(self.admin)
        invalid_state = self.client.post(url, data=draft, content_type="application/json")

        self.assertEqual(denied.status_code, 404)
        self.assertEqual(invalid_state.status_code, 409)
        connector.assert_not_called()

    @patch("api.edk.views.JiraConnector")
    def test_owner_can_refresh_tracking_but_cannot_discover_another_edk(self, connector):
        self.application.jira_issue_key = "UAV-10"
        self.application.jira_url = "http://jira.local/browse/UAV-10"
        self.application.save(update_fields=["jira_issue_key", "jira_url"])
        foreign_user = get_user_model().objects.create_user(
            username="foreign-edk-user",
            password="StrongPass123!",
        )
        Group.objects.get(name=EDK_ROLE_GROUPS["applicant"]).user_set.add(foreign_user)
        jira = connector.return_value
        jira.server_url = "http://jira.local"
        jira.issue.return_value = self.jira_issue(
            "UAV-10",
            "Güncel uçuş özeti",
            "Devam Ediyor",
            "indeterminate",
        )
        jira.search_issues.return_value = [
            self.jira_issue("UAV-11", "Motor kontrolü", "Kapalı", "done")
        ]
        url = reverse(
            "edk-application-jira-refresh",
            kwargs={"application_id": self.application.id},
        )

        self.client.force_login(self.user)
        refreshed = self.client.post(url)
        self.client.force_login(foreign_user)
        hidden = self.client.post(url)

        self.assertEqual(refreshed.status_code, 200)
        self.assertEqual(refreshed.json()["summary"], "Güncel uçuş özeti")
        self.assertTrue(refreshed.json()["all_subtasks_closed"])
        self.assertIsNotNone(refreshed.json()["last_synced_at"])
        self.assertEqual(hidden.status_code, 404)

    @patch("api.edk.views.JiraConnector")
    def test_refresh_normalizes_jira_provider_failure(self, connector):
        self.application.jira_issue_key = "UAV-10"
        self.application.save(update_fields=["jira_issue_key"])
        connector.return_value.issue.side_effect = JiraConnectorError(
            "token=secret http://jira.internal /private/cert.pem"
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "edk-application-jira-refresh",
                kwargs={"application_id": self.application.id},
            )
        )

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json(), {"detail": "Jira takip bilgisi yenilenemedi."})
        self.assertNotIn("jira.internal", response.content.decode())

    @patch("api.edk.views.JiraConnector")
    def test_inactive_owner_cannot_refresh_tracking(self, connector):
        self.application.jira_issue_key = "UAV-10"
        self.application.save(update_fields=["jira_issue_key"])
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "edk-application-jira-refresh",
                kwargs={"application_id": self.application.id},
            )
        )

        self.assertEqual(response.status_code, 403)
        connector.assert_not_called()

    def test_same_jira_task_cannot_be_linked_to_two_edk_records(self):
        other = EDKApplication.objects.create(
            applicant=self.user,
            aircraft_name="Anka",
        )
        link_edk_jira_issue(
            application=self.application,
            issue_key="UAV-10",
            url="http://jira.local/browse/UAV-10",
            summary="Uçuş hazırlığı",
        )

        with self.assertRaises(EDKJiraConflict):
            link_edk_jira_issue(
                application=other,
                issue_key="UAV-10",
                url="http://jira.local/browse/UAV-10",
                summary="Başka EDK",
            )

    @staticmethod
    def jira_issue(key, summary, status_name, status_category):
        return Mock(
            key=key,
            fields=Mock(
                summary=summary,
                status=Mock(
                    name=status_name,
                    statusCategory=Mock(key=status_category),
                ),
            ),
        )

    @patch("api.edk.views.publish_jira_draft")
    def test_publish_endpoint_requires_staff(self, publish):
        publish.return_value = {
            "status": "created",
            "message": "",
            "task": {"key": "UAV-10", "url": "http://jira.local/browse/UAV-10"},
            "subtasks": [],
        }
        payload = {
            "task": {"project_key": "UAV", "summary": "Uçuş hazırlığı"},
            "subtasks": [],
        }
        request_payload = {**payload, "jsession": "admin-session-123"}
        self.client.force_login(self.user)
        denied = self.client.post(
            reverse("edk-jira-publish"),
            data=request_payload,
            content_type="application/json",
        )
        self.client.force_login(self.admin)
        allowed = self.client.post(
            reverse("edk-jira-publish"),
            data=request_payload,
            content_type="application/json",
        )

        self.assertEqual(denied.status_code, 403)
        self.assertEqual(allowed.status_code, 201)
        publish.assert_called_once()
        self.assertEqual(publish.call_args.args[0], payload)

    @patch("api.edk.views.publish_jira_draft")
    def test_publish_endpoint_rejects_enabled_subtask_without_summary(self, publish):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("edk-jira-publish"),
            data={
                "task": {"project_key": "UAV", "summary": "Uçuş hazırlığı"},
                "subtasks": [{"enabled": True, "summary": "   "}],
                "jsession": "admin-session-123",
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {"subtasks": ["Dahil edilen her alt görev için özet zorunludur."]},
        )
        publish.assert_not_called()

    @patch("api.edk.views.JiraConnector")
    def test_application_publish_requires_a_valid_jsession(self, connector):
        self.client.force_login(self.user)
        url = reverse(
            "edk-application-jira-publish",
            kwargs={"application_id": self.application.id},
        )
        payload = build_jira_draft(self.extracted)

        missing = self.client.post(url, data=payload, content_type="application/json")
        invalid = self.client.post(
            url,
            data={**payload, "jsession": "session; injected=value"},
            content_type="application/json",
        )

        self.assertEqual(missing.status_code, 400)
        self.assertEqual(missing.json(), {"jsession": ["Bu alan zorunlu."]})
        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(
            invalid.json(),
            {"jsession": ["Yalnızca JSESSIONID çerezinin geçerli değerini girin."]},
        )
        connector.assert_not_called()

    @patch("api.edk.views.publish_jira_draft")
    def test_publish_endpoint_does_not_echo_jira_provider_detail(self, publish):
        publish.side_effect = JiraConnectorError(
            "token=secret http://jira.internal/rest /private/cert.pem"
        )
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("edk-jira-publish"),
            data={
                "task": {"project_key": "UAV", "summary": "Uçuş hazırlığı"},
                "subtasks": [],
                "jsession": "admin-session-123",
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()["detail"], "Jira aktarımı tamamlanamadı.")
        self.assertNotIn("jira.internal", response.content.decode())
