from django.test import SimpleTestCase

from .common.network import InvalidServiceUrl, validated_browser_origin, validated_http_url
from .services.jira_connector import JiraConfig, JiraConnectorError


class OutboundUrlValidationTests(SimpleTestCase):
    def test_accepts_http_and_https_urls(self):
        self.assertEqual(
            validated_http_url("http://127.0.0.1:11434"),
            "http://127.0.0.1:11434",
        )
        self.assertEqual(
            validated_http_url("https://ai.example.test/v1"),
            "https://ai.example.test/v1",
        )

    def test_rejects_non_http_and_credential_bearing_urls(self):
        invalid_urls = (
            "file:///etc/passwd",
            "ftp://ai.example.test/model",
            "https://user:secret@ai.example.test/v1",
            "https://ai.example.test:invalid/v1",
            "https://ai.example.test/v1#fragment",
        )

        for value in invalid_urls:
            with self.subTest(value=value), self.assertRaises(InvalidServiceUrl):
                validated_http_url(value)

    def test_jira_configuration_uses_the_same_outbound_url_boundary(self):
        config = JiraConfig(
            server="file:///tmp/fake-jira",
            personal_access_token="test-only-token",
        )

        with self.assertRaises(JiraConnectorError):
            config.validate()

    def test_local_service_policy_accepts_private_hosts_and_rejects_public_hosts(self):
        self.assertEqual(
            validated_http_url(
                "http://192.168.10.20:11434",
                setting_name="OLLAMA_BASE_URL",
                require_local=True,
            ),
            "http://192.168.10.20:11434",
        )

        with self.assertRaisesMessage(InvalidServiceUrl, "loopback/private"):
            validated_http_url(
                "https://ai.example.test",
                setting_name="OLLAMA_BASE_URL",
                require_local=True,
            )

    def test_remote_and_browser_boundaries_can_require_https(self):
        with self.assertRaisesMessage(InvalidServiceUrl, "HTTPS"):
            validated_http_url(
                "http://ai.example.test",
                require_https_for_remote=True,
            )
        with self.assertRaisesMessage(InvalidServiceUrl, "HTTPS"):
            validated_browser_origin(
                "http://frontend.example.test",
                setting_name="CORS_ALLOWED_ORIGINS",
                require_https=True,
            )
        with self.assertRaisesMessage(InvalidServiceUrl, "path/query"):
            validated_browser_origin(
                "https://frontend.example.test/app?mode=prod",
                setting_name="CORS_ALLOWED_ORIGINS",
                require_https=True,
            )
