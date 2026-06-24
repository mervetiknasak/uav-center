# UAV Center

Python Django backend ve Vue 3 + Naive UI frontend ile lokal belge işleme uygulaması.

## Dizinler

- `backend/`: Django API uygulaması
- `frontend/`: Vue 3 arayüzü

## Özellikler

- PDF, DOCX, XLSX, PPTX, TXT, CSV ve MD dosyalarını yükleme
- Django REST Framework tabanlı API
- Dosyaları lokal diskte `backend/media/` altında saklama
- Belgeden metin çıkarma
- Çıkarılan metni lokal AI işlem katmanına gönderme
- Varsayılan lokal özetleyici ile özet, anahtar kelime ve metrik üretme
- İsteğe bağlı Ollama veya OpenAI uyumlu lokal bağlantı ile Qwen2.5 kullanma
- Whisper için lokal Python modeli veya lokal HTTP transkripsiyon servisi wrapper'ı

## Backend

Backend Python 3.11 ile çalışacak şekilde hedeflenmiştir. Launcher yeni sanal
ortam oluştururken Python 3.11 yorumlayıcısını arar.

Tüm geliştirme ortamını tek komutla başlatmak için:

```bash
python3 launcher.py
```

Launcher backend sanal ortamını ve frontend paketlerini kontrol eder, eksikse kurar,
Django migration'larını çalıştırır ve backend ile frontend servislerini birlikte
ayağa kaldırır. Windows'ta aynı komut `py launcher.py` veya `python launcher.py`
olarak çalıştırılabilir.

Yalnızca bir tarafı çalıştırmak için:

```bash
python3 launcher.py --backend-only
python3 launcher.py --frontend-only
python3 launcher.py --backend-port 18000 --frontend-port 5174
```

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8000
```

Backend ayarları [backend/.env](/Users/testuser/Projects/uav-center/backend/.env) dosyasından okunur.

API endpoint'leri:

```text
http://localhost:8000/api/health/
http://localhost:8000/api/documents/
http://localhost:8000/api/documents/upload/
http://localhost:8000/api/documents/<id>/
```

DRF yanıt formatı:

- `GET /api/documents/`: belge listesi
- `POST /api/documents/upload/`: `file` ve `prompt` alanlarıyla işlenen belge objesi
- `GET /api/documents/<id>/`: çıkarılan metin dahil belge objesi
- `DELETE /api/documents/<id>/`: belge kaydını ve lokal dosyayı siler

Örnek upload:

```bash
curl -F "file=@ornek.pdf" \
  -F "prompt=Bu belgedeki riskleri ve aksiyonları listele." \
  http://localhost:8000/api/documents/upload/
```

## Lokal AI Ayarları

Varsayılan mod dış servise bağlanmaz:

`backend/.env` içinde `AI_PROVIDER=local`

Qwen2.5:14b modelini Ollama ile kullanmak için:

`backend/.env` içinde `AI_PROVIDER=ollama` ve `QWEN_MODEL=qwen2.5:14b`

Ollama `http://127.0.0.1:11434` adresinde çalışmalıdır. Farklı adres için:

`backend/.env` içinde `OLLAMA_BASE_URL=http://127.0.0.1:11434`

OpenAI uyumlu lokal bir Qwen servisine bağlanmak için:

```env
AI_PROVIDER=local_llm
LOCAL_LLM_BASE_URL=http://127.0.0.1:8001
QWEN_MODEL=qwen2.5:14b
LOCAL_LLM_API_KEY=
```

Wrapper `POST /v1/chat/completions` endpoint'ini bekler.

Whisper transkripsiyon wrapper'ı için iki seçenek vardır:

```env
WHISPER_CONNECTION=local
WHISPER_MODEL=base
```

Bu modda backend ortamında `openai-whisper` paketi bulunmalıdır. Lokal HTTP servis
kullanmak için:

```env
WHISPER_CONNECTION=http
WHISPER_BASE_URL=http://127.0.0.1:8002
WHISPER_MODEL=whisper-1
```

HTTP modunda wrapper OpenAI uyumlu `POST /v1/audio/transcriptions` endpoint'ine
multipart dosya gönderir.

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend API proxy hedefi [frontend/.env](/Users/testuser/Projects/uav-center/frontend/.env) dosyasındaki `VITE_API_TARGET` değeriyle belirlenir.

Varsayılan frontend adresi:

```text
http://localhost:5173
```

Frontend, geliştirme modunda Django API'ye `/api` proxy'si üzerinden bağlanır.
