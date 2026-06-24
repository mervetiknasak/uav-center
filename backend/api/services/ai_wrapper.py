import json
import mimetypes
import uuid
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from django.conf import settings


class AIProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class AIWrapperConfig:
    provider: str
    ollama_base_url: str
    qwen_model: str
    local_llm_base_url: str
    local_llm_api_key: str
    whisper_connection: str
    whisper_model: str
    whisper_base_url: str

    @classmethod
    def from_settings(cls):
        return cls(
            provider=getattr(settings, "AI_PROVIDER", "local").lower(),
            ollama_base_url=getattr(settings, "OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/"),
            qwen_model=getattr(settings, "QWEN_MODEL", "qwen2.5:14b"),
            local_llm_base_url=getattr(settings, "LOCAL_LLM_BASE_URL", "http://127.0.0.1:8001").rstrip("/"),
            local_llm_api_key=getattr(settings, "LOCAL_LLM_API_KEY", ""),
            whisper_connection=getattr(settings, "WHISPER_CONNECTION", "local").lower(),
            whisper_model=getattr(settings, "WHISPER_MODEL", "base"),
            whisper_base_url=getattr(settings, "WHISPER_BASE_URL", "http://127.0.0.1:8002").rstrip("/"),
        )


class AIWrapper:
    def __init__(self, config=None):
        self.config = config or AIWrapperConfig.from_settings()

    def generate(self, prompt, system_prompt="", model=None, temperature=0.2):
        provider = self.config.provider
        if provider == "ollama":
            return self._generate_with_ollama(prompt, system_prompt, model, temperature)
        if provider in {"local_llm", "local-http", "local_http"}:
            return self._generate_with_local_llm(prompt, system_prompt, model, temperature)

        raise AIProviderError(
            "AI_PROVIDER qwen için 'ollama' veya 'local_llm' olmalı. "
            "Servissiz özet için mevcut local özetleyici kullanılabilir."
        )

    def transcribe(self, audio_path, language=None):
        connection = self.config.whisper_connection
        if connection == "local":
            return self._transcribe_with_local_whisper(audio_path, language)
        if connection in {"http", "local_http", "local-http"}:
            return self._transcribe_with_http_whisper(audio_path, language)

        raise AIProviderError("WHISPER_CONNECTION 'local' veya 'http' olmalı.")

    def _generate_with_ollama(self, prompt, system_prompt, model, temperature):
        payload = {
            "model": model or self.config.qwen_model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if system_prompt:
            payload["system"] = system_prompt

        data = _post_json(f"{self.config.ollama_base_url}/api/generate", payload, timeout=180)
        return {
            "provider": "ollama",
            "model": payload["model"],
            "response": data.get("response", "").strip(),
            "raw": data,
        }

    def _generate_with_local_llm(self, prompt, system_prompt, model, temperature):
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model or self.config.qwen_model,
            "messages": messages,
            "temperature": temperature,
            "stream": False,
        }
        headers = {}
        if self.config.local_llm_api_key:
            headers["Authorization"] = f"Bearer {self.config.local_llm_api_key}"

        data = _post_json(
            f"{self.config.local_llm_base_url}/v1/chat/completions",
            payload,
            headers=headers,
            timeout=180,
        )
        response = ""
        choices = data.get("choices") or []
        if choices:
            response = (choices[0].get("message") or {}).get("content", "")

        return {
            "provider": "local_llm",
            "model": payload["model"],
            "response": response.strip(),
            "raw": data,
        }

    def _transcribe_with_local_whisper(self, audio_path, language):
        try:
            import whisper
        except ImportError as exc:
            raise AIProviderError(
                "Lokal Whisper için 'openai-whisper' paketi kurulu olmalı "
                "veya WHISPER_CONNECTION=http kullanılmalı."
            ) from exc

        model = whisper.load_model(self.config.whisper_model)
        result = model.transcribe(str(audio_path), language=language)
        return {
            "provider": "local_whisper",
            "model": self.config.whisper_model,
            "text": (result.get("text") or "").strip(),
            "language": result.get("language"),
            "segments": result.get("segments", []),
        }

    def _transcribe_with_http_whisper(self, audio_path, language):
        url = f"{self.config.whisper_base_url}/v1/audio/transcriptions"
        fields = {"model": self.config.whisper_model}
        if language:
            fields["language"] = language

        data = _post_multipart(url, {"file": Path(audio_path)}, fields, timeout=180)
        return {
            "provider": "http_whisper",
            "model": self.config.whisper_model,
            "text": (data.get("text") or "").strip(),
            "language": data.get("language"),
            "raw": data,
        }


def _post_json(url, payload, headers=None, timeout=120):
    request_headers = {"Content-Type": "application/json"}
    request_headers.update(headers or {})
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=request_headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise AIProviderError(f"AI bağlantısı başarısız: {exc}") from exc


def _post_multipart(url, files, fields=None, timeout=120):
    boundary = f"----uav-center-{uuid.uuid4().hex}"
    body = bytearray()

    for name, value in (fields or {}).items():
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"))
        body.extend(str(value).encode("utf-8"))
        body.extend(b"\r\n")

    for name, path in files.items():
        filename = path.name
        content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(
            (
                f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'
                f"Content-Type: {content_type}\r\n\r\n"
            ).encode("utf-8")
        )
        body.extend(path.read_bytes())
        body.extend(b"\r\n")

    body.extend(f"--{boundary}--\r\n".encode("utf-8"))
    request = urllib.request.Request(
        url,
        data=bytes(body),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise AIProviderError(f"Whisper bağlantısı başarısız: {exc}") from exc
