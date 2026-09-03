from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase, override_settings
from django.urls import reverse

from .edk.jira import build_jira_draft, fetch_jira_tracking, publish_jira_draft
from .edk.roles import EDK_ROLE_GROUPS
from .edk.services import EDKJiraConflict, link_edk_jira_issue
from .models import EDKApplication, PanelResponsible, Project, ProjectPanel
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
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse(
                "edk-application-jira-publish",
                kwargs={"application_id": self.application.id},
            ),
            data=build_jira_draft(self.extracted),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        self.application.refresh_from_db()
        self.assertEqual(self.application.jira_issue_key, "UAV-10")
        self.assertEqual(self.application.jira_url, "http://jira.local/browse/UAV-10")
        self.assertEqual(self.application.jira_summary, "Uçuş hazırlığı")
        self.assertEqual(response.json()["tracking"]["subtask_total"], 1)
        self.assertFalse(response.json()["tracking"]["all_subtasks_closed"])

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
            data=build_jira_draft(self.extracted),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        self.application.refresh_from_db()
        self.assertEqual(self.application.jira_issue_key, "UAV-10")
        self.assertIsNone(self.application.jira_last_synced_at)
        self.assertIn("daha sonra yenilenmelidir", response.json()["message"])

    @patch("api.edk.views.JiraConnector")
    def test_application_publish_requires_admin_and_an_approved_minutes_upload(self, connector):
        url = reverse(
            "edk-application-jira-publish",
            kwargs={"application_id": self.application.id},
        )
        draft = build_jira_draft(self.extracted)
        self.client.force_login(self.user)
        denied = self.client.post(url, data=draft, content_type="application/json")
        self.application.minutes_file_name = ""
        self.application.save(update_fields=["minutes_file_name"])
        self.client.force_login(self.admin)
        invalid_state = self.client.post(url, data=draft, content_type="application/json")

        self.assertEqual(denied.status_code, 403)
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
        self.client.force_login(self.user)
        denied = self.client.post(
            reverse("edk-jira-publish"),
            data=payload,
            content_type="application/json",
        )
        self.client.force_login(self.admin)
        allowed = self.client.post(
            reverse("edk-jira-publish"),
            data=payload,
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
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {"subtasks": ["Dahil edilen her alt görev için özet zorunludur."]},
        )
        publish.assert_not_called()

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
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()["detail"], "Jira aktarımı tamamlanamadı.")
        self.assertNotIn("jira.internal", response.content.decode())
