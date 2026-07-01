from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import TestCase

from .models import PanelResponsible, Project, ProjectPanel
from .services.word_to_jira import build_jira_draft, publish_jira_draft


class WordToJiraTests(TestCase):
    def setUp(self):
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

    @patch("api.services.word_to_jira.JiraConnector")
    def test_publishes_parent_before_subtask(self, connector_class):
        jira = Mock()
        jira.config = SimpleNamespace(server="http://jira.local")
        jira.search_issues.return_value = []
        jira.create_issue.side_effect = [Mock(key="UAV-10"), Mock(key="UAV-11")]
        connector_class.return_value = jira
        draft = build_jira_draft(self.extracted)

        result = publish_jira_draft(draft)

        self.assertEqual(result["task"]["key"], "UAV-10")
        self.assertEqual(result["subtasks"][0]["key"], "UAV-11")
        subtask_call = jira.create_issue.call_args_list[1].kwargs
        self.assertEqual(subtask_call["parent_key"], "UAV-10")
        self.assertEqual(subtask_call["assignee_username"], "ada.local")
        self.assertEqual(subtask_call["custom_fields"], {"duedate": "2026-07-10"})
