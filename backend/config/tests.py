import json
import logging
import os
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import patch

from django.http import HttpResponse
from django.test import Client, RequestFactory, SimpleTestCase, override_settings

from .logging import (
    RequestContextFilter,
    SafeJsonFormatter,
    SafeTextFormatter,
    SensitiveDataFilter,
)
from .middleware import RequestIdMiddleware
from .request_context import get_request_id


class RequestIdMiddlewareTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = RequestIdMiddleware(lambda _request: HttpResponse("ok"))

    def test_preserves_safe_incoming_request_id_on_response(self):
        request = self.factory.get("/api/health/", HTTP_X_REQUEST_ID="trace-123")

        response = self.middleware(request)

        self.assertEqual(response.headers["X-Request-ID"], "trace-123")
        self.assertEqual(request.request_id, "trace-123")
        self.assertEqual(get_request_id(), "-")

    def test_replaces_invalid_request_id(self):
        request = self.factory.get("/api/health/", HTTP_X_REQUEST_ID="invalid value\n")

        response = self.middleware(request)

        generated = response.headers["X-Request-ID"]
        self.assertRegex(generated, r"^[0-9a-f]{32}$")

    @patch("config.middleware.perf_counter", side_effect=[10.0, 10.125])
    def test_logs_structured_request_completion_without_query_string(self, _clock):
        request = self.factory.get("/api/health/?verbose=true")
        request.user = SimpleNamespace(is_authenticated=True, pk=42)

        with self.assertLogs("config.request", level="INFO") as captured:
            self.middleware(request)

        record = captured.records[0]
        self.assertEqual(record.event, "request_completed")
        self.assertEqual(record.http_method, "GET")
        self.assertEqual(record.path, "/api/health/")
        self.assertEqual(record.status_code, 200)
        self.assertEqual(record.duration_ms, 125.0)
        self.assertEqual(record.user_id, 42)

    @patch("config.middleware.perf_counter", side_effect=[20.0, 20.25])
    def test_logs_uncaught_exception_as_500_before_reraising(self, _clock):
        middleware = RequestIdMiddleware(lambda _request: 1 / 0)
        request = self.factory.get("/api/failure/")

        with self.assertLogs("config.request", level="ERROR") as captured:
            with self.assertRaises(ZeroDivisionError):
                middleware(request)

        record = captured.records[0]
        self.assertEqual(record.event, "request_completed")
        self.assertEqual(record.status_code, 500)
        self.assertEqual(record.levelno, logging.ERROR)
        self.assertIsNone(record.exc_info)
        self.assertEqual(record.safe_exception["type"], "ZeroDivisionError")
        self.assertTrue(record.safe_exception["frames"])
        self.assertEqual(get_request_id(), "-")

    @patch("config.middleware.perf_counter", side_effect=[30.0, 30.01])
    def test_logs_5xx_response_at_error_level(self, _clock):
        middleware = RequestIdMiddleware(lambda _request: HttpResponse(status=503))

        with self.assertLogs("config.request", level="ERROR") as captured:
            response = middleware(self.factory.get("/api/health/ready/"))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(captured.records[0].status_code, 503)
        self.assertEqual(captured.records[0].levelno, logging.ERROR)
        self.assertFalse(captured.records[0].exc_info)


class LoggingTests(SimpleTestCase):
    def test_json_formatter_includes_context_and_redacts_sensitive_extras(self):
        record = logging.LogRecord(
            name="config.test",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="request completed",
            args=(),
            exc_info=None,
        )
        record.event = "request_completed"
        record.request_id = "trace-456"
        record.api_token = "secret-value"
        record.metadata = {
            "headers": {"authorization": "Bearer nested-secret"},
            "items": [{"password": "nested-password"}],
        }
        RequestContextFilter().filter(record)
        SensitiveDataFilter().filter(record)

        payload = json.loads(SafeJsonFormatter().format(record))

        self.assertEqual(payload["event"], "request_completed")
        self.assertEqual(payload["request_id"], "trace-456")
        self.assertNotIn("secret-value", json.dumps(payload))
        self.assertEqual(record.__dict__["api_token"], "[REDACTED]")
        metadata = record.__dict__["metadata"]
        self.assertEqual(metadata["headers"]["authorization"], "[REDACTED]")
        self.assertEqual(metadata["items"][0]["password"], "[REDACTED]")

    def test_formatters_never_render_raw_exception_payload_or_absolute_path(self):
        try:
            raise RuntimeError(
                "token=super-secret https://internal.local /private/tmp/customer.txt"
            )
        except RuntimeError:
            exception_info = sys.exc_info()

        record = logging.LogRecord(
            name="config.test",
            level=logging.ERROR,
            pathname=__file__,
            lineno=1,
            msg="request failed token=message-secret pilot@example.com",
            args=(),
            exc_info=exception_info,
        )
        RequestContextFilter().filter(record)
        SensitiveDataFilter().filter(record)

        json_output = SafeJsonFormatter().format(record)
        text_output = SafeTextFormatter(
            "{levelname} request_id={request_id} {message}",
            style="{",
        ).format(record)

        for output in (json_output, text_output):
            self.assertNotIn("super-secret", output)
            self.assertNotIn("message-secret", output)
            self.assertNotIn("pilot@example.com", output)
            self.assertNotIn("/private/tmp", output)
        payload = json.loads(json_output)
        self.assertEqual(payload["exception"]["type"], "RuntimeError")
        self.assertNotIn("message", payload["exception"])


class EmailConfigurationTests(SimpleTestCase):
    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend",
        EMAIL_TIMEOUT=17,
    )
    def test_smtp_backend_receives_the_bounded_timeout(self):
        from django.core.mail import get_connection

        self.assertEqual(get_connection().timeout, 17)


class CorsConfigurationTests(SimpleTestCase):
    def test_notification_idempotency_header_is_allowed_in_preflight(self):
        response = Client().options(
            "/api/technical-documents/1/notify/",
            HTTP_ORIGIN="http://localhost:5173",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS=("content-type,idempotency-key,x-csrftoken"),
        )

        self.assertEqual(response.status_code, 200)
        allowed_headers = {
            header.strip().lower()
            for header in response.headers["Access-Control-Allow-Headers"].split(",")
        }
        self.assertIn("idempotency-key", allowed_headers)


class ProductionSettingsTests(SimpleTestCase):
    @staticmethod
    def run_settings_import(**overrides):
        environment = os.environ.copy()
        environment.update(
            {
                "APP_ENV": "production",
                "DJANGO_DEBUG": "false",
                "DJANGO_ALLOWED_HOSTS": "uav.example.test",
                "DJANGO_SECRET_KEY": "aB3!z" * 12,
                "EMAIL_BACKEND": "django.core.mail.backends.smtp.EmailBackend",
                "OCR_ALLOW_MODEL_DOWNLOAD": "false",
                "JIRA_VERIFY_SSL": "true",
            }
        )
        environment.update(overrides)
        return subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import json; from config import settings; "
                    "print(json.dumps({"
                    "'debug': settings.DEBUG, "
                    "'ssl': settings.SECURE_SSL_REDIRECT, "
                    "'session': settings.SESSION_COOKIE_SECURE, "
                    "'csrf': settings.CSRF_COOKIE_SECURE, "
                    "'hsts': settings.SECURE_HSTS_SECONDS, "
                    "'preload': settings.SECURE_HSTS_PRELOAD, "
                    "'cors': settings.CORS_ALLOWED_ORIGINS, "
                    "'csrf_origins': settings.CSRF_TRUSTED_ORIGINS}))"
                ),
            ],
            cwd=os.path.dirname(os.path.dirname(__file__)),
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_production_defaults_are_secure(self):
        completed = self.run_settings_import()

        self.assertEqual(completed.returncode, 0, completed.stderr)
        values = json.loads(completed.stdout.strip())
        self.assertEqual(
            values,
            {
                "debug": False,
                "ssl": True,
                "session": True,
                "csrf": True,
                "hsts": 31_536_000,
                "preload": False,
                "cors": [],
                "csrf_origins": [],
            },
        )

    def test_hsts_preload_requires_explicit_opt_in(self):
        completed = self.run_settings_import(DJANGO_SECURE_HSTS_PRELOAD="true")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(json.loads(completed.stdout.strip())["preload"])

    def test_production_rejects_missing_secret(self):
        completed = self.run_settings_import(DJANGO_SECRET_KEY="")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("DJANGO_SECRET_KEY", completed.stderr)

    def test_production_rejects_non_delivery_email_backend(self):
        completed = self.run_settings_import(
            EMAIL_BACKEND="django.core.mail.backends.console.EmailBackend"
        )

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("EMAIL_BACKEND", completed.stderr)

    def test_production_rejects_disabled_https_controls(self):
        overrides = {
            "DJANGO_SECURE_SSL_REDIRECT": "false",
            "DJANGO_SESSION_COOKIE_SECURE": "false",
            "DJANGO_CSRF_COOKIE_SECURE": "false",
            "DJANGO_SECURE_HSTS_SECONDS": "0",
        }

        for name, value in overrides.items():
            with self.subTest(name=name):
                completed = self.run_settings_import(**{name: value})
                self.assertNotEqual(completed.returncode, 0)
                self.assertIn(name, completed.stderr)

    def test_production_rejects_wildcard_host_and_insecure_external_origins(self):
        cases = (
            ("DJANGO_ALLOWED_HOSTS", "*"),
            ("DJANGO_ALLOWED_HOSTS", ".example.test"),
            ("DJANGO_ALLOWED_HOSTS", "*.example.test"),
            ("CORS_ALLOWED_ORIGINS", "http://frontend.example.test"),
            ("CSRF_TRUSTED_ORIGINS", "http://frontend.example.test"),
            ("JIRA_SERVER", "http://jira.example.test"),
        )

        for name, value in cases:
            with self.subTest(name=name):
                completed = self.run_settings_import(**{name: value})
                self.assertNotEqual(completed.returncode, 0)
                self.assertIn(name, completed.stderr)

    def test_production_remote_ai_requires_explicit_opt_in_and_https(self):
        without_opt_in = self.run_settings_import(
            OLLAMA_BASE_URL="https://ai.example.test",
        )
        insecure_opt_in = self.run_settings_import(
            AI_ALLOW_REMOTE_SERVICES="true",
            OLLAMA_BASE_URL="http://ai.example.test",
        )
        secure_opt_in = self.run_settings_import(
            AI_ALLOW_REMOTE_SERVICES="true",
            OLLAMA_BASE_URL="https://ai.example.test",
        )

        self.assertNotEqual(without_opt_in.returncode, 0)
        self.assertIn("OLLAMA_BASE_URL", without_opt_in.stderr)
        self.assertNotEqual(insecure_opt_in.returncode, 0)
        self.assertIn("HTTPS", insecure_opt_in.stderr)
        self.assertEqual(secure_opt_in.returncode, 0, secure_opt_in.stderr)

    def test_settings_reject_non_positive_document_resource_limit(self):
        completed = self.run_settings_import(DOCUMENT_MAX_PDF_PAGES="0")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("DOCUMENT_MAX_PDF_PAGES", completed.stderr)

    def test_settings_reject_non_positive_external_service_timeout(self):
        for name in ("EMAIL_TIMEOUT", "TECHNICAL_NOTIFICATION_PENDING_TIMEOUT"):
            with self.subTest(name=name):
                completed = self.run_settings_import(**{name: "0"})

                self.assertNotEqual(completed.returncode, 0)
                self.assertIn(name, completed.stderr)
