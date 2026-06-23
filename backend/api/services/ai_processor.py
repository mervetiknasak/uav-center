import json
import re
import urllib.error
import urllib.request

from django.conf import settings


def process_document_text(text, filename, prompt):
    provider = getattr(settings, "AI_PROVIDER", "local")
    if provider == "ollama":
        try:
            return _process_with_ollama(text, filename, prompt)
        except RuntimeError as exc:
            fallback = _process_locally(text, filename, prompt)
            fallback["provider_error"] = str(exc)
            return fallback

    return _process_locally(text, filename, prompt)


def _process_locally(text, filename, prompt):
    words = re.findall(r"\w+", text, flags=re.UNICODE)
    sentences = _split_sentences(text)
    keywords = _extract_keywords(words)
    preview = " ".join(sentences[:4]) if sentences else "Dosyadan işlenebilir metin çıkarılamadı."

    return {
        "provider": "local",
        "filename": filename,
        "prompt": prompt,
        "response": (
            "Lokal sağlayıcı aktif. Belge metni çıkarıldı; aşağıdaki ön analiz, "
            "kullanıcı prompt'u ile birlikte gerçek yerel model katmanına aktarılmaya hazır."
        ),
        "preview": preview,
        "keywords": keywords,
        "metrics": {
            "characters": len(text),
            "words": len(words),
            "sentences": len(sentences),
        },
    }


def _process_with_ollama(text, filename, prompt):
    full_prompt = (
        f"Kullanıcı isteği:\n{prompt}\n\n"
        f"Dosya: {filename}\n\n"
        f"Belge metni:\n{text[:24000]}"
    )
    payload = json.dumps(
        {
            "model": getattr(settings, "OLLAMA_MODEL", "llama3.1"),
            "prompt": full_prompt,
            "stream": False,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{settings.OLLAMA_BASE_URL}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Ollama bağlantısı başarısız: {exc}") from exc

    return {
        "provider": "ollama",
        "filename": filename,
        "model": getattr(settings, "OLLAMA_MODEL", "llama3.1"),
        "prompt": prompt,
        "response": data.get("response", "").strip(),
    }


def _split_sentences(text):
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]


def _extract_keywords(words):
    stopwords = {
        "ve",
        "veya",
        "ile",
        "için",
        "bir",
        "bu",
        "da",
        "de",
        "the",
        "and",
        "or",
        "to",
        "of",
        "in",
    }
    counts = {}
    for word in words:
        normalized = word.lower()
        if len(normalized) < 4 or normalized in stopwords:
            continue
        counts[normalized] = counts.get(normalized, 0) + 1

    ranked = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    return [word for word, _count in ranked[:10]]
