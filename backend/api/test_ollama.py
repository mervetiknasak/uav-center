import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from .serializers import OllamaChatRequestSerializer
from .services.ollama_service import OllamaService


class OllamaChatSerializerTests(SimpleTestCase):
    @override_settings(OLLAMA_MODEL="gemma4:e4b")
    def test_builds_multimodal_thinking_payload_with_recommended_sampling(self):
        serializer = OllamaChatRequestSerializer(
            data={
                "messages": [
                    {
                        "role": "user",
                        "content": "Görseli analiz et",
                        "images": ["data:image/png;base64,aGVsbG8="],
                    }
                ],
                "system_prompt": "<|think|> Türkçe yanıt ver.",
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        payload = serializer.to_ollama_payload()

        self.assertEqual(payload["model"], "gemma4:e4b")
        self.assertEqual(payload["messages"][0]["role"], "system")
        self.assertEqual(payload["messages"][1]["images"], ["aGVsbG8="])
        self.assertTrue(payload["think"])
        self.assertEqual(payload["options"]["temperature"], 1.0)
        self.assertEqual(payload["options"]["top_p"], 0.95)
        self.assertEqual(payload["options"]["top_k"], 64)

    def test_rejects_invalid_tool_schema_container(self):
        serializer = OllamaChatRequestSerializer(
            data={"messages": [{"role": "user", "content": "Test"}], "tools": {}}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("tools", serializer.errors)


@override_settings(
    OLLAMA_MODEL="gemma4:e4b",
    OLLAMA_BASE_URL="http://127.0.0.1:11434",
    OLLAMA_TIMEOUT=30,
    OLLAMA_PULL_TIMEOUT=60,
)
class OllamaServiceTests(SimpleTestCase):
    @patch.object(OllamaService, "_json_request")
    def test_status_matches_configured_and_running_model(self, request):
        request.side_effect = [
            {"version": "0.32.6"},
            {"models": [{"name": "gemma4:e4b", "size": 123}]},
            {"models": [{"model": "gemma4:e4b", "size_vram": 100}]},
        ]

        result = OllamaService().status()

        self.assertTrue(result["connected"])
        self.assertTrue(result["installed"])
        self.assertTrue(result["loaded"])
        self.assertEqual(result["configured_model"], "gemma4:e4b")


@override_settings(
    OLLAMA_MODEL="gemma4:e4b",
    OLLAMA_BASE_URL="http://127.0.0.1:11434",
    OLLAMA_TIMEOUT=30,
    OLLAMA_PULL_TIMEOUT=60,
)
class OllamaApiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="operator", password="test-password", is_active=True
        )
        self.admin = get_user_model().objects.create_user(
            username="admin", password="test-password", is_active=True, is_staff=True
        )

    @patch.object(OllamaService, "status")
    def test_authenticated_user_can_read_status(self, service_status):
        service_status.return_value = {
            "connected": True,
            "configured_model": "gemma4:e4b",
            "installed": True,
        }
        self.client.force_login(self.user)

        response = self.client.get(reverse("ollama-status"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["installed"])

    @patch.object(OllamaService, "pull")
    def test_only_admin_can_pull_model(self, pull):
        pull.return_value = {"status": "success"}
        self.client.force_login(self.user)
        denied = self.client.post(reverse("ollama-pull"))
        self.client.force_login(self.admin)
        allowed = self.client.post(reverse("ollama-pull"))

        self.assertEqual(denied.status_code, 403)
        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(allowed.json()["model"], "gemma4:e4b")

    @patch.object(OllamaService, "chat_stream")
    def test_chat_endpoint_streams_ndjson(self, chat_stream):
        chat_stream.return_value = iter(
            [
                {"message": {"role": "assistant", "content": "Merhaba"}, "done": False},
                {"message": {"role": "assistant", "content": "!"}, "done": True},
            ]
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("ollama-chat"),
            data={"messages": [{"role": "user", "content": "Selam"}]},
            content_type="application/json",
        )
        chunks = b"".join(response.streaming_content).decode("utf-8").splitlines()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/x-ndjson")
        self.assertEqual(json.loads(chunks[0])["message"]["content"], "Merhaba")
