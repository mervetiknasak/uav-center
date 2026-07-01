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
- Admin tarafından yönetilen proje, alt panel ve panel sorumlusu organizasyon yapısı
- Aktif kullanıcılar için salt okunur organizasyon görünümü
- Proje sekmeleri, KPI kartları ve gelişmiş filtrelerle teknik doküman dashboardu
- Doküman durum/revizyon/yayın/termin takibi ve denetlenebilir durum geçmişi
- Bir teknik dokümanı aynı projedeki birden fazla panelle ilişkilendirme
- Panel sorumlularına alıcı önizlemeli e-posta bildirimi ve bildirim geçmişi

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
python3 launcher.py --no-reload
```

Launcher, Django kaynak dosyalarındaki değişiklikleri varsayılan olarak izler ve
backend'i otomatik yeniden yükler. Bu davranış gerektiğinde `--no-reload` ile
kapatılabilir.

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
http://localhost:8000/api/organization/projects/
http://localhost:8000/api/technical-documents/
http://localhost:8000/api/word-to-jira/parse/
```

DRF yanıt formatı:

- `GET /api/documents/`: belge listesi
- `POST /api/documents/upload/`: `file` ve `prompt` alanlarıyla işlenen belge objesi
- `GET /api/documents/<id>/`: çıkarılan metin dahil belge objesi
- `DELETE /api/documents/<id>/`: belge kaydını ve lokal dosyayı siler
- `GET /api/organization/projects/`: projeleri alt panelleri ve sorumlularıyla listeler
- Organizasyon API'sindeki `POST`, `PATCH` ve `DELETE` işlemleri yalnızca admin kullanıcılarına açıktır
- `GET|POST /api/technical-documents/`: teknik doküman listesi ve admin oluşturma işlemi
- `GET|PATCH|DELETE /api/technical-documents/<id>/`: detay, statü dahil güncelleme ve silme
- `POST /api/technical-documents/<id>/notify/`: bağlı panellerdeki e-posta adresi bulunan sorumlulara bildirim gönderme
- `POST /api/word-to-jira/parse/`: `.docx` tablo hücrelerini 0 tabanlı global, tablo, satır ve sütun indeksleriyle okuma
- `POST /api/word-to-jira/publish/`: düzenlenen toplantı taslağından bir Jira Task ve ona bağlı Sub-task kayıtları oluşturma

Yerel demo dokümanlarını mevcut projelere idempotent olarak eklemek için:

```bash
cd backend
python manage.py seed_technical_documents
```

E-posta geliştirme ortamında varsayılan olarak konsola yazılır. SMTP kullanımı için
`backend/.env` içinde `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`,
`EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS` ve
`DEFAULT_FROM_EMAIL` değerleri tanımlanabilir.

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

## Jira Connector

`api.services.jira_connector.JiraConnector`, diğer backend modüllerinin
kullanabileceği Jira servis katmanıdır. Issue oluşturma/güncelleme/silme, JQL
arama, atama ve durum geçişleri; yorum, dosya eki, worklog, issue linki,
takipçi ve oy işlemleri; proje, kullanıcı, sürüm ve bileşen sorgularını kapsar.

Jira Cloud için:

```env
JIRA_SERVER=https://kurum.atlassian.net
JIRA_EMAIL=kullanici@kurum.com
JIRA_API_TOKEN=atlassian-api-token
JIRA_VERIFY_SSL=true
JIRA_TIMEOUT=30
JIRA_MEETING_PROJECT_KEY=MOM
```

Jira Data Center/Server için personal access token kullanılabilir:

```env
JIRA_SERVER=https://jira.kurum.local
JIRA_PERSONAL_ACCESS_TOKEN=token
```

Alternatif olarak `JIRA_USERNAME` ve `JIRA_PASSWORD` ile basic auth
kullanılabilir. Örnek:

```python
from api.services.jira_connector import JiraConnector

jira = JiraConnector()
issue = jira.create_issue(
    project_key="UAV",
    summary="Uçuş öncesi kontrol",
    issue_type="Task",
    labels=["operation"],
)
jira.transition_issue(issue.key, "In Progress")
```

`PanelResponsible.username` genel kullanıcı kimliğidir ve toplantı tutanağı
aktarımında sorumlu ataması için de kullanılır. Ana Task tutanak bilgilerini
açıklamasında taşır; her seçili aksiyon maddesi ana Task altında Sub-task olarak
oluşturulur. Tutanak ve aksiyon etiketleri yeniden aktarımda mükerrer kayıtları
önlemek ve yarım kalan alt görevleri güvenle tekrar denemek için kullanılır.
Jira proje anahtarı organizasyon kayıtlarından türetilmez; taslaklarda varsayılan
olarak `MOM`, `JIRA_MEETING_PROJECT_KEY` tanımlanmışsa onun değeri kullanılır.

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
