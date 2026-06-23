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
- İsteğe bağlı Ollama bağlantısı ile yerel LLM kullanma

## Backend

```bash
cd backend
python3 -m venv .venv
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

Ollama kullanmak için:

`backend/.env` içinde `AI_PROVIDER=ollama` ve `OLLAMA_MODEL=llama3.1`

Ollama `http://127.0.0.1:11434` adresinde çalışmalıdır. Farklı adres için:

`backend/.env` içinde `OLLAMA_BASE_URL=http://127.0.0.1:11434`

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
