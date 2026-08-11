import json
import urllib.error
import urllib.request

from django.conf import settings

from .ai_wrapper import AIProviderError


class OllamaService:
    """Small, dependency-free gateway for the local Ollama HTTP API."""

    def __init__(self, base_url=None, model=None, timeout=None):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.timeout = timeout or settings.OLLAMA_TIMEOUT

    def status(self):
        try:
            version = self._json_request("GET", "/api/version", timeout=5)
            tags = self._json_request("GET", "/api/tags", timeout=10)
            running = self._json_request("GET", "/api/ps", timeout=10)
        except AIProviderError as exc:
            return {
                "connected": False,
                "base_url": self.base_url,
                "configured_model": self.model,
                "installed": False,
                "loaded": False,
                "error": str(exc),
                "models": [],
                "running_models": [],
            }

        models = tags.get("models") or []
        running_models = running.get("models") or []
        return {
            "connected": True,
            "base_url": self.base_url,
            "version": version.get("version", ""),
            "configured_model": self.model,
            "installed": any(self._same_model(item, self.model) for item in models),
            "loaded": any(self._same_model(item, self.model) for item in running_models),
            "models": models,
            "running_models": running_models,
            "recommended_options": {"temperature": 1.0, "top_p": 0.95, "top_k": 64},
        }

    def pull(self, model=None):
        selected_model = model or self.model
        return self._json_request(
            "POST",
            "/api/pull",
            {"model": selected_model, "stream": False},
            timeout=settings.OLLAMA_PULL_TIMEOUT,
        )

    def unload(self, model=None):
        selected_model = model or self.model
        return self._json_request(
            "POST",
            "/api/generate",
            {"model": selected_model, "keep_alive": 0},
        )

    def show(self, model=None):
        return self._json_request("POST", "/api/show", {"model": model or self.model})

    def chat_stream(self, payload):
        request = self._request("POST", "/api/chat", payload, timeout=self.timeout)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                for raw_line in response:
                    line = raw_line.decode("utf-8").strip()
                    if not line:
                        continue
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError as exc:
                        raise AIProviderError("Ollama geçersiz bir akış yanıtı döndürdü.") from exc
        except urllib.error.HTTPError as exc:
            detail = self._http_error_detail(exc)
            raise AIProviderError(f"Ollama HTTP {exc.code}: {detail}") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise AIProviderError(f"Ollama bağlantısı başarısız: {exc}") from exc

    def _json_request(self, method, path, payload=None, timeout=None):
        request = self._request(method, path, payload, timeout=timeout)
        try:
            with urllib.request.urlopen(request, timeout=timeout or self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = self._http_error_detail(exc)
            raise AIProviderError(f"Ollama HTTP {exc.code}: {detail}") from exc
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            raise AIProviderError(f"Ollama bağlantısı başarısız: {exc}") from exc

    def _request(self, method, path, payload=None, timeout=None):
        del timeout  # Kept in the signature to make call sites self-documenting.
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"} if data is not None else {}
        return urllib.request.Request(
            f"{self.base_url}{path}", data=data, headers=headers, method=method
        )

    @staticmethod
    def _http_error_detail(exc):
        try:
            data = json.loads(exc.read().decode("utf-8"))
            return data.get("error") or data.get("detail") or str(data)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return str(exc.reason)

    @staticmethod
    def _same_model(item, expected):
        name = item.get("model") or item.get("name") or ""
        if name == expected:
            return True
        if ":" not in expected and name == f"{expected}:latest":
            return True
        return False
