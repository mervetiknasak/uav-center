from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import PanelResponsible, Project, ProjectPanel
from .services.jira_connector import JiraConnectorError
from .services.word_to_jira import build_jira_draft, publish_jira_draft


@override_settings(
    JIRA_SERVER="http://jira.local",
    JIRA_PERSONAL_ACCESS_TOKEN="test-token",
)
class WordToJiraTests(TestCase):
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

    @patch("api.meeting_minutes.views.publish_jira_draft")
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
            reverse("word-to-jira-publish"),
            data=payload,
            content_type="application/json",
        )
        self.client.force_login(self.admin)
        allowed = self.client.post(
            reverse("word-to-jira-publish"),
            data=payload,
            content_type="application/json",
        )

        self.assertEqual(denied.status_code, 403)
        self.assertEqual(allowed.status_code, 201)
        publish.assert_called_once()
        self.assertEqual(publish.call_args.args[0], payload)

    @patch("api.meeting_minutes.views.publish_jira_draft")
    def test_publish_endpoint_rejects_enabled_subtask_without_summary(self, publish):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("word-to-jira-publish"),
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

    @patch("api.meeting_minutes.views.publish_jira_draft")
    def test_publish_endpoint_does_not_echo_jira_provider_detail(self, publish):
        publish.side_effect = JiraConnectorError(
            "token=secret http://jira.internal/rest /private/cert.pem"
        )
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("word-to-jira-publish"),
            data={
                "task": {"project_key": "UAV", "summary": "Uçuş hazırlığı"},
                "subtasks": [],
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()["detail"], "Jira aktarımı tamamlanamadı.")
        self.assertNotIn("jira.internal", response.content.decode())
