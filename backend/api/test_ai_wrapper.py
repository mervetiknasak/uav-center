import json
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from .services.ai_processor import process_document_text
from .services.ai_wrapper import AIWrapper


class _FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class AIWrapperTests(SimpleTestCase):
    @override_settings(AI_PROVIDER="ollama", OLLAMA_MODEL="gemma4:e4b")
    @patch("urllib.request.urlopen")
    def test_ollama_generation_uses_configured_model(self, urlopen):
        urlopen.return_value = _FakeResponse({"response": "hazir"})

        result = AIWrapper().generate("Merhaba")
        request = urlopen.call_args.args[0]
        payload = json.loads(request.data.decode("utf-8"))

        self.assertEqual(payload["model"], "gemma4:e4b")
        self.assertEqual(result["provider"], "ollama")
        self.assertEqual(result["response"], "hazir")

    @override_settings(AI_PROVIDER="local")
    def test_local_provider_keeps_builtin_summary(self):
        result = process_document_text(
            "İHA bakım kaydı tamamlandı. Batarya kontrol edildi.",
            "rapor.txt",
            "Özetle",
        )

        self.assertEqual(result["provider"], "local")
        self.assertIn("metrics", result)
