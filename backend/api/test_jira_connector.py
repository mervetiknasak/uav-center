import sys
from types import ModuleType
from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings

from .services.jira_connector import JiraConfig, JiraConnector, JiraConnectorError


class JiraConnectorTests(SimpleTestCase):
    def setUp(self):
        self.client = Mock()
        self.connector = JiraConnector(client=self.client)

    def test_create_issue_builds_jira_fields_and_custom_fields(self):
        self.client.create_issue.return_value = Mock(key="UAV-42")

        result = self.connector.create_issue(
            project_key="UAV",
            summary="Motor kontrolü",
            issue_type="Task",
            description="Sol motor titreşim üretiyor.",
            assignee="account-123",
            priority="High",
            labels=["flight"],
            components=["Propulsion"],
            custom_fields={"customfield_10001": "Hangar 2"},
        )

        fields = self.client.create_issue.call_args.kwargs["fields"]
        self.assertEqual(result.key, "UAV-42")
        self.assertEqual(fields["project"], {"key": "UAV"})
        self.assertEqual(fields["assignee"], {"accountId": "account-123"})
        self.assertEqual(fields["components"], [{"name": "Propulsion"}])
        self.assertEqual(fields["customfield_10001"], "Hangar 2")

    def test_create_issue_supports_local_jira_username(self):
        self.connector.create_issue(
            project_key="UAV",
            summary="Motor kontrolü",
            issue_type="Sub-task",
            assignee_username="ada",
            parent_key="UAV-10",
        )

        fields = self.client.create_issue.call_args.kwargs["fields"]
        self.assertEqual(fields["assignee"], {"name": "ada"})
        self.assertEqual(fields["parent"], {"key": "UAV-10"})

    def test_search_issues_passes_pagination_and_fields(self):
        self.connector.search_issues(
            "project = UAV ORDER BY created DESC",
            start_at=10,
            max_results=25,
            fields=["summary", "status"],
        )

        self.client.search_issues.assert_called_once_with(
            "project = UAV ORDER BY created DESC",
            startAt=10,
            maxResults=25,
            fields=["summary", "status"],
            expand=None,
            validate_query=True,
        )

    def test_update_issue_fetches_and_updates_resource(self):
        issue = Mock()
        self.client.issue.return_value = issue

        result = self.connector.update_issue(
            "UAV-42",
            fields={"summary": "Yeni özet"},
            notify_users=False,
        )

        issue.update.assert_called_once_with(
            fields={"summary": "Yeni özet"},
            notify=False,
        )
        self.assertIs(result, issue)

    def test_add_worklog_uses_supported_estimate_parameters(self):
        self.connector.add_worklog(
            "UAV-42",
            "2h",
            new_estimate="1d",
            adjust_estimate="new",
        )

        self.client.add_worklog.assert_called_once_with(
            "UAV-42",
            timeSpent="2h",
            newEstimate="1d",
            adjustEstimate="new",
        )

    def test_api_errors_are_normalized(self):
        error = RuntimeError("permission denied")
        error.status_code = 403
        error.text = "Forbidden"
        self.client.issue.side_effect = error

        with self.assertRaises(JiraConnectorError) as context:
            self.connector.issue("UAV-42")

        self.assertEqual(context.exception.status_code, 403)
        self.assertIn("HTTP 403", str(context.exception))
        self.assertIn("Forbidden", str(context.exception))

    def test_json_field_errors_are_parsed_from_response(self):
        response = Mock(
            status_code=400,
            url="https://jira.example/rest/api/2/issue",
            headers={},
            text='{"errorMessages":["Invalid issue"],"errors":{"summary":"Required"}}',
        )
        response.json.return_value = {
            "errorMessages": ["Invalid issue"],
            "errors": {"summary": "Required"},
        }
        error = RuntimeError("request failed")
        error.response = response
        self.client.create_issue.side_effect = error

        with self.assertRaises(JiraConnectorError) as context:
            self.connector.create_issue(
                project_key="UAV",
                summary="Test",
                issue_type="Task",
            )

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(
            context.exception.response_text,
            "Invalid issue; summary: Required",
        )

    def test_html_error_is_reduced_to_readable_bounded_text(self):
        response = Mock(
            status_code=502,
            url="https://jira.example/rest/api/2/issue/UAV-42",
            headers={"Content-Type": "text/html"},
            text=(
                "<html><head><title>Bad Gateway</title>"
                "<style>secret-css</style></head><body>"
                "<h1>Proxy unavailable</h1><script>secret-js</script>"
                "<p>Please retry later.</p></body></html>"
            ),
        )
        response.json.side_effect = ValueError("not json")
        error = RuntimeError("request failed")
        error.response = response
        self.client.issue.side_effect = error

        with self.assertRaises(JiraConnectorError) as context:
            self.connector.issue("UAV-42")

        self.assertEqual(
            context.exception.response_text,
            "Bad Gateway: Proxy unavailable Please retry later.",
        )
        self.assertNotIn("secret", str(context.exception))

    def test_auth_denial_header_takes_precedence(self):
        response = Mock(
            status_code=403,
            url="https://jira.example/rest/api/2/myself",
            headers={"X-Authentication-Denied-Reason": "CAPTCHA required"},
            text="<html><body>Login page</body></html>",
        )
        response.json.side_effect = ValueError("not json")
        error = RuntimeError("request failed")
        error.response = response
        self.client.myself.side_effect = error

        with self.assertRaises(JiraConnectorError) as context:
            self.connector.check_connection()

        self.assertEqual(context.exception.response_text, "CAPTCHA required")

    def test_personal_access_token_is_passed_as_token_auth(self):
        jira_module = ModuleType("jira")
        jira_constructor = Mock(return_value=Mock())
        jira_module.JIRA = jira_constructor
        config = JiraConfig(
            server="https://jira.example.com",
            personal_access_token="pat-secret",
        )

        with patch.dict(sys.modules, {"jira": jira_module}):
            _client = JiraConnector(config=config).client

        jira_constructor.assert_called_once_with(
            options={
                "server": "https://jira.example.com",
                "verify": True,
            },
            timeout=30,
            token_auth="pat-secret",
        )

    @override_settings(
        JIRA_SERVER="https://example.atlassian.net",
        JIRA_EMAIL="pilot@example.com",
        JIRA_API_TOKEN="secret",
    )
    def test_config_is_loaded_from_django_settings(self):
        config = JiraConfig.from_settings()

        self.assertEqual(config.server, "https://example.atlassian.net")
        self.assertEqual(config.email, "pilot@example.com")
        self.assertEqual(config.api_token, "secret")

    def test_config_requires_server_and_credentials(self):
        with self.assertRaises(JiraConnectorError):
            JiraConfig(server="").validate()

        with self.assertRaises(JiraConnectorError):
            JiraConfig(server="https://jira.example.com").validate()
