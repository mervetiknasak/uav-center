from django.test import SimpleTestCase

from .redaction import (
    REDACTED_EMAIL,
    REDACTED_PATH,
    REDACTED_SECRET,
    REDACTED_URL,
    redact_sensitive_text,
    safe_exception_message,
)


class SafeErrorRedactionTests(SimpleTestCase):
    def test_exception_redacts_credentials_urls_paths_email_and_tokens(self):
        unsafe = RuntimeError(
            "password=super-secret Bearer bearer-secret "
            "api_key='api-secret' token=token-secret "
            "http://admin:pass@10.0.0.8:11434/api/tags "
            "jira.internal:8080/rest/api "
            "/Users/operator/private/report.docx "
            r"C:\Users\Operator\private\report.docx "
            "pilot@example.com"
        )

        result = safe_exception_message(unsafe, max_length=500)

        for sensitive_value in (
            "super-secret",
            "bearer-secret",
            "api-secret",
            "token-secret",
            "10.0.0.8",
            "jira.internal",
            "/Users/operator",
            r"C:\Users\Operator",
            "pilot@example.com",
        ):
            self.assertNotIn(sensitive_value, result)
        self.assertIn(REDACTED_SECRET, result)
        self.assertIn(REDACTED_URL, result)
        self.assertIn(REDACTED_PATH, result)
        self.assertIn(REDACTED_EMAIL, result)

    def test_redaction_handles_quoted_paths_and_enforces_max_length(self):
        result = redact_sensitive_text(
            'failed at "/Users/Operator Name/private file.txt" ' + ("x" * 500),
            max_length=80,
        )

        self.assertNotIn("Operator Name", result)
        self.assertIn(REDACTED_PATH, result)
        self.assertLessEqual(len(result), 80)

    def test_exception_with_empty_detail_still_has_bounded_audit_value(self):
        result = safe_exception_message(RuntimeError(), max_length=32)

        self.assertTrue(result.startswith("RuntimeError:"))
        self.assertLessEqual(len(result), 32)
