import re

from django.conf import settings

from .ai_wrapper import AIProviderError, AIWrapper


def process_document_text(text, filename, prompt):
    provider = getattr(settings, "AI_PROVIDER", "local")
    if provider in {"ollama", "local_llm", "local-http", "local_http"}:
        try:
            return _process_with_model(text, filename, prompt)
        except AIProviderError as exc:
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


def _process_with_model(text, filename, prompt):
    system_prompt = (
        "Sen UAV Center içinde çalışan yerel Gemma belge analiz asistanısın. "
        "Yanıtlarını Türkçe, net ve uygulanabilir maddeler halinde ver."
    )
    full_prompt = (
        f"Kullanıcı isteği:\n{prompt}\n\n"
        f"Dosya: {filename}\n\n"
        f"Belge metni:\n{text[:24000]}"
    )
    result = AIWrapper().generate(full_prompt, system_prompt=system_prompt)

    return {
        "provider": result["provider"],
        "filename": filename,
        "model": result["model"],
        "prompt": prompt,
        "response": result["response"],
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
