from unittest.mock import MagicMock, patch

from django.db import OperationalError
from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory

from .readiness import readiness_check


class ReadinessCheckTests(SimpleTestCase):
    def setUp(self):
        self.request = APIRequestFactory().get("/api/health/ready/")

    @patch("api.common.readiness.connection")
    def test_returns_ready_after_database_probe(self, database_connection):
        cursor = MagicMock()
        database_connection.cursor.return_value.__enter__.return_value = cursor

        response = readiness_check(self.request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"status": "ready", "database": "ok"})
        cursor.execute.assert_called_once_with("SELECT 1")
        cursor.fetchone.assert_called_once_with()

    @patch("api.common.readiness.connection")
    def test_returns_service_unavailable_when_database_probe_fails(self, database_connection):
        database_connection.cursor.side_effect = OperationalError("database unavailable")

        with patch("api.common.readiness.logger"):
            response = readiness_check(self.request)

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.data,
            {"status": "unavailable", "database": "unavailable"},
        )
