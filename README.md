# UAV Center

Python/Django backend ve Vue 3 + Naive UI frontend ile geliştirilen, local-first
belge işleme ve mühendislik operasyonları platformu.

## Dizinler

- `backend/`: Django API uygulaması
- `frontend/`: Vue 3 arayüzü
- `docs/`: mimari, entegrasyon ve operasyon belgeleri

Sistem feature-first modular monolith olarak düzenlenmiştir. Domain sınırları,
bağımlılık yönü, veri sahipliği ve genişletme kuralları için
[`docs/architecture.md`](docs/architecture.md); katkı akışı için
[`CONTRIBUTING.md`](CONTRIBUTING.md) ve bağlayıcı agent kuralları için
[`AGENTS.md`](AGENTS.md) dosyasına bakın.

## Özellikler

- PDF, DOCX, XLSX, PPTX, TXT, CSV, MD ve yaygın resim dosyalarını yükleme
- Türkçe ve İngilizce yerel OCR, taranmış PDF/gömülü görsel okuma ve e-posta adresi çıkarma
- Django REST Framework tabanlı API
- Dosyaları lokal diskte `backend/media/` altında saklama
- Belgeden metin çıkarma
- Çıkarılan metni lokal AI işlem katmanına gönderme
- Kaynak kimlikli, kalıcı belge parçaları üzerinde BM25 retrieval ve grounded RAG yanıtları
- Kalıcı, yeniden denemeli asenkron job kuyruğu ve paralel worker desteği
- Kullanıcı bazında izole edilen belge/job listesi, ilerleme ve hata takibi
- Sunucu kontrolleri ile kullanıcıların arayüzden ekleyebildiği tekrar kullanılabilir analiz kontrolleri
- Kaynak atıfları ve kullanıcı bazlı analiz çalıştırma geçmişi
- Varsayılan lokal özetleyici ile özet, anahtar kelime ve metrik üretme
- İsteğe bağlı Ollama veya OpenAI uyumlu yerel model bağlantısı
- Ollama üzerinde Gemma 4 E4B için akışlı, çok turlu ve multimodal AI Studio
- Whisper için lokal Python modeli veya lokal HTTP transkripsiyon servisi wrapper'ı
- Admin tarafından yönetilen proje, alt panel ve panel sorumlusu organizasyon yapısı
- Aktif kullanıcılar için salt okunur organizasyon görünümü
- Proje sekmeleri, KPI kartları ve gelişmiş filtrelerle teknik doküman dashboardu
- Doküman durum/revizyon/yayın/termin takibi ve denetlenebilir durum geçmişi
- Bir teknik dokümanı aynı projedeki birden fazla panelle ilişkilendirme
- Panel sorumlularına alıcı önizlemeli e-posta bildirimi ve bildirim geçmişi
- Teknik doküman termin/inceleme tarihleri, bekleyen iş akışları ve uçuş izni
  geçerliliklerini birleştiren Operasyonel Takvim
- Uçuş izni formları dahil klasör bazlı 14 mühendislik süreci ve 35 sürümlü FM Word şablonu
- Mühendislik form kayıtlarında güvenli doküman eki ve indirilebilir Word çıktısı

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
python3 launcher.py --job-workers 4
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

`requirements.txt`, OCR ve lokal Whisper dahil tam runtime'ı kurar. Yalnız API,
statik analiz ve test ortamı için daha hafif `requirements-base.txt` ile
`requirements-dev.txt` birlikte kullanılabilir; CI bu profili kullanır.

Backend ayarları `backend/.env` dosyasından okunur.
[`backend/.env.example`](backend/.env.example) geliştirme şablonu ve production
değişken kontrol listesidir; içindeki `development`, HTTP, güvensiz cookie ve
`HSTS=0` değerleri production'a aynen kopyalanmaz. `APP_ENV=production` güçlü
secret, sınırlı host, SSL redirect, secure cookie, HSTS ve teslimat yapan e-posta
backend'i olmadan fail-fast olur. Browser originleri veya Jira URL'si tanımlanırsa
production'da HTTPS olmak zorundadır. Gerçek secret değerlerini commit etmeyin.

API endpoint'leri:

```text
http://localhost:8000/api/health/
http://localhost:8000/api/health/ready/
http://localhost:8000/api/documents/
http://localhost:8000/api/documents/upload/
http://localhost:8000/api/documents/<id>/
http://localhost:8000/api/documents/<id>/rag/query/
http://localhost:8000/api/documents/<id>/controls/run/
http://localhost:8000/api/analysis-controls/
http://localhost:8000/api/jobs/
http://localhost:8000/api/operational-alerts/
http://localhost:8000/api/form-processes/
http://localhost:8000/api/organization/projects/
http://localhost:8000/api/technical-documents/
http://localhost:8000/api/edk/applications/
http://localhost:8000/api/ai/ollama/status/
http://localhost:8000/api/ai/ollama/chat/
```

DRF yanıt formatı:

- `GET /api/documents/`: kullanıcının belge listesi; staff bütün kayıtları denetleyebilir
- `POST /api/documents/upload/`: `file`, `prompt`, `use_ocr` ve `use_ai` alanlarıyla belgeyi sıraya alır; `202 Accepted` ile job ve bekleyen belgeyi döndürür
- `GET /api/documents/<id>/`: sahibine ait, çıkarılan metin dahil belge objesi
- `DELETE /api/documents/<id>/`: sahibine ait belge kaydını ve lokal dosyayı siler
- `POST /api/documents/<id>/rag/query/`: `query` ve opsiyonel `top_k` ile kaynaklı RAG yanıtı üretir
- `POST /api/documents/<id>/controls/run/`: `control_ids` ile sunucu ve kullanıcı kontrollerini çalıştırır
- `GET|POST /api/analysis-controls/`: hazır kontrolleri listeler veya kullanıcıya özel kontrol oluşturur
- `PATCH|DELETE /api/analysis-controls/<id>/`: yalnızca kontrol sahibinin kaydını günceller veya siler
- `GET /api/jobs/`: oturum sahibinin son joblarını listeler; `status` ve `limit` parametrelerini destekler
- `GET /api/jobs/<uuid>/`: yalnızca oturum sahibinin job detayını döndürür
- `POST /api/jobs/<uuid>/cancel/`: sırada bekleyen ve oturum sahibine ait jobı iptal eder
- `GET /api/operational-alerts/`: aktif kullanıcıya teknik doküman termin/inceleme,
  14 günü dolduran inceleme/revizyon ve onaylı uçuş izni geçerlilik uyarılarını;
  gecikmiş, 7 gün içinde ve 30 gün içinde özetleriyle döndürür
- `GET /api/form-processes/templates/`: süreç, FM şablonu ve dinamik alan kataloğunu döndürür
- `GET|POST /api/form-processes/`: uçuş izinleri dahil paylaşımlı mühendislik form kayıtlarını listeler veya oluşturur
- `GET|PATCH|DELETE /api/form-processes/<id>/`: mühendislik form kaydını okur, günceller veya siler
- `GET /api/form-processes/<id>/attachment/`: doğrulanmış form ekini sunucu MIME politikasıyla indirir
- `GET /api/form-processes/<id>/generated-document/`: kaynak FM şablonunu ve doğrulanmış kayıt alanlarını içeren Word çıktısı üretir
- `GET /api/organization/projects/`: projeleri alt panelleri ve sorumlularıyla listeler
- Organizasyon API'sindeki `POST`, `PATCH` ve `DELETE` işlemleri yalnızca admin kullanıcılarına açıktır
- `GET|POST /api/technical-documents/`: teknik doküman listesi ve admin oluşturma işlemi
- `GET|PATCH|DELETE /api/technical-documents/<id>/`: detay, statü dahil güncelleme ve silme
- `POST /api/technical-documents/<id>/notify/`: staff kullanıcının bağlı panel sorumlularına, zorunlu ve istek başına benzersiz `Idempotency-Key` başlığıyla bildirim göndermesi
- `GET|POST /api/edk/applications/`: EDK rollerine göre başvuru listesi ve Başvuru Sahibi rolüyle yeni başvuru oluşturma
- `POST /api/edk/applications/<id>/decision/`: Onaylayıcı rolüyle bekleyen başvuruyu onaylama veya gerekçeli reddetme
- `POST /api/edk/applications/<id>/minutes/parse/`: yalnız başvuru sahibi ve onaylanmış EDK kaydı için `.docx` toplantı tutanağını okuma
- `POST /api/edk/jira/publish/`: staff kullanıcının düzenlenen toplantı taslağından bir Jira Task ve ona bağlı Sub-task kayıtları oluşturması

Yerel demo dokümanlarını mevcut projelere idempotent olarak eklemek için:

```bash
cd backend
python manage.py seed_technical_documents
```

E-posta geliştirme ortamında varsayılan olarak konsola yazılır. SMTP kullanımı için
`backend/.env` içinde `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`,
`EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_TIMEOUT`,
`TECHNICAL_NOTIFICATION_PENDING_TIMEOUT`, `EMAIL_USE_TLS` ve `DEFAULT_FROM_EMAIL`
değerleri tanımlanabilir. `APP_ENV=production` ortamı,
bildirimi teslim etmeyen console/dummy/file/locmem backend'leri reddeder; SMTP veya
kurumun onaylı teslimat backend'i açıkça yapılandırılmalıdır.

Teknik doküman bildirim endpoint'i `Idempotency-Key` başlığını zorunlu tutar.
Frontend aynı doküman ve payload için sonucu belirsiz kalan transport retry'ında
aynı UUID'yi korur; sunucunun başarısız teslimatı kesin olarak kaydettiği durumda
yeni deneme yeni anahtar alır. Aynı anahtar farklı payload ile kullanılırsa
`409 Conflict` döner. SMTP teslimi ile başarı audit'inin kalıcılaştırılması arasındaki
process-crash penceresinde mutlak exactly-once garantisi yoktur; `pending` kayıt
`TECHNICAL_NOTIFICATION_PENDING_TIMEOUT` (varsayılan 300 saniye) sonrasında
`unknown` durumuna alınır ve operasyonel olarak uzlaştırılmadan yeni anahtarla
tekrar gönderim yapılmamalıdır.

## Operasyonel Takvim

**İşlemler → Operasyonel Takvim** ekranı teknik doküman `due_date` ve
`review_date` alanlarını, inceleme/revizyon durumunda geçirilen süreyi ve onaylı
uçuş izinlerinin `valid_until` tarihini tek salt-okunur görünümde birleştirir.
Tarih değerlendirmesi `Europe/Istanbul` yerel gününe göre yapılır; bugün dahil
7 günlük kayıtlar kritik, sonraki 23 günlük kayıtlar yaklaşan, tarihi geçenler
gecikmiş olarak gösterilir. `in_review` veya `changes_requested` durumunda 14 günü
tamamlayan teknik dokümanlar ayrıca bekleyen iş akışı uyarısı üretir.

Bu endpoint otomatik e-posta göndermez ve kalıcı uyarı kaydı oluşturmaz. Staff
kullanıcı “Bildirim hazırla” eylemiyle teknik doküman ekranındaki mevcut alıcı
önizlemeli ve idempotent bildirim akışına yönlendirilir. Diğer kullanıcılar aynı
paylaşımlı operasyonel kayıtları görebilir, ancak bildirim gönderemez.

## Mühendislik Form Süreçleri

**Süreçler → Formlar** çalışma alanı, `Formlar` envanterindeki klasörleri süreç ve
`FM` ile başlayan DOCX dosyalarını sürümlü şablon olarak sunar. Katalogda uçuş
izinleri dahil 14 süreç altında 35 şablon bulunur. `FM.QUA.0579`, `FM.QUA.0580`
ve `FM.QUA.0581` uçuş izni sürecinin şablonlarıdır; kayıtları da diğer formlar
gibi `FormProcessRecord` içinde tutulur. Her şablon; kaynak formdaki başlık, boş hücre
ve yer tutuculardan çıkarılan alan şemasına sahiptir. Backend yalnız seçilen
şablonun alanlarını kabul eder; zorunlu alan, veri tipi, tarih, seçim ve uzunluk
sınırlarını yan etkiden önce doğrular.

Kayıtlar paylaşımlı operasyonel veridir ve aktif kullanıcılar tarafından yönetilir.
`GET /api/form-processes/templates/` arayüzün dinamik form kataloğudur. Word indirme
akışı kaynak DOCX'i docxtpl ile açar, kaynak sayfaları korur ve doğrulanmış alanları
aynı dokümanın sonuna “Süreç Kayıt Bilgileri” bölümü olarak ekler. Böylece kaynak
form revizyonu görünür kalırken veri tabanındaki tam kayıt denetlenebilir biçimde
çıktıya taşınır.

Form eklerinde en fazla 15 MB boyutunda PDF, DOCX, XLSX, JPG/JPEG ve PNG kabul
edilir. İstemcinin bildirdiği MIME türü güvenilir sayılmaz; dosya yapısı sunucuda
incelenir. Eski ayrı uçuş izni kayıtları ileri yönlü migration ile karşılık gelen
FM şablonlarına ve aynı form eki alanına taşınır.

SessionAuthentication kullanan komut satırı istemcisi önce `/api/auth/csrf/`
yanıtındaki `csrfToken` değerini `CSRF_TOKEN` olarak almalı, aynı `cookies.txt`
cookie jar'ı ile `/api/auth/login/` üzerinden giriş yapmalıdır. Aşağıdaki upload
örnekleri bu doğrulanmış oturumun hazır olduğunu varsayar:

```bash
curl -b cookies.txt -H "X-CSRFToken: ${CSRF_TOKEN}" \
  -F "file=@ornek.pdf" \
  -F "prompt=Bu belgedeki riskleri ve aksiyonları listele." \
  http://localhost:8000/api/documents/upload/
```

Yükleme katmanı dosyayı kalıcılaştırmadan önce uzantı ve toplam boyuta ek olarak
OOXML zorunlu parçalarını, arşiv öğesi/açılmış boyut sınırını, PDF sayfa sayısını
ve görsel kare/piksel sınırını doğrular. Güvenli varsayılanlar gerektiğinde şu
ortam değişkenleriyle daraltılabilir:

```env
DOCUMENT_MAX_UPLOAD_SIZE=26214400
DOCUMENT_MAX_ARCHIVE_ENTRIES=2000
DOCUMENT_MAX_UNCOMPRESSED_SIZE=104857600
DOCUMENT_MAX_PDF_PAGES=500
OCR_MAX_IMAGES=50
OCR_MAX_PIXELS=20000000
```

Bu değerler pozitif olmalıdır; geçersiz kaynak limitleri uygulama başlangıcında
reddedilir.

## Asenkron Job Kuyruğu

Belge yükleme isteği OCR ve AI sonucunu beklemez. Dosya ve bekleyen belge kaydı
oluşturulduktan sonra kalıcı bir job döner; `run_job_worker` süreci işi arka planda
tamamlar. Launcher worker'ı otomatik başlatır. Worker'ı ayrıca çalıştırmak için:

```bash
cd backend
python manage.py run_job_worker
python manage.py run_job_worker --once
```

Aynı veritabanını kullanan birden fazla worker güvenli biçimde paralel çalışabilir.
Yük altında launcher `--job-workers 4` gibi bir değerle başlatılabilir. Başarısız
joblar üstel gecikmeyle yeniden denenir; yarım kalan worker jobları zaman aşımından
sonra tekrar kuyruğa alınır. İlgili ortam ayarları:

```env
JOB_MAX_ATTEMPTS=3
JOB_RETRY_BASE_SECONDS=15
JOB_STALE_TIMEOUT=7200
```

Üretimde çok sayıda paralel worker için SQLite yerine satır düzeyinde eşzamanlı
yazmayı destekleyen bir veritabanı kullanılması önerilir.

## Yerel OCR

Belge İşleme panelindeki OCR seçeneği PNG, JPG/JPEG, WebP, BMP ve TIFF
resimlerini; metin içermeyen PDF sayfalarını; DOCX, PPTX ve XLSX dosyalarına
gömülü görselleri EasyOCR ile yerelde okur. Türkçe ve İngilizce birlikte
kullanılır. OCR metninde bulunan geçerli e-posta adresleri sonuç ekranında
tekrarsız olarak listelenir.

API'de `use_ocr` varsayılan olarak `false`, `use_ai` ise `true` değerindedir.
AI kapatıldığında prompt zorunlu değildir:

```bash
curl -b cookies.txt -H "X-CSRFToken: ${CSRF_TOKEN}" \
  -F "file=@mail-ekran-goruntusu.png" \
  -F "use_ocr=true" \
  -F "use_ai=false" \
  http://localhost:8000/api/documents/upload/
```

Varsayılan `AI_ALLOW_REMOTE_SERVICES=false` politikası OCR, prompt, belge metni ve
AI Studio görsellerini loopback/private servis sınırında tutar. Bu ayarı bilinçli
olarak açmak veri aktarım güven sınırını değiştirir; production'da uzak AI URL'leri
HTTPS olmak zorundadır. EasyOCR modellerini ilk
kullanımdan önce `backend/.env` içinde geçici olarak
`OCR_ALLOW_MODEL_DOWNLOAD=true` yapıp backend sanal ortamında şu komutu bir kez
çalıştırarak `backend/ocr_models/` dizinine hazırlayın:

```bash
python manage.py shell -c "from api.services.ocr_processor import get_reader; get_reader()"
```

İndirme tamamlandıktan sonra `.env` içinde `OCR_ALLOW_MODEL_DOWNLOAD=false`
kullanarak çalışma anında ağ erişimini kapalı tutun. Bu değer varsayılan olarak
zaten `false` değerindedir. Model konumu ve kaynak limitleri şu ayarlarla
değiştirilebilir:

```env
OCR_MODEL_DIR=/yerel/model/dizini
OCR_ALLOW_MODEL_DOWNLOAD=false
OCR_USE_GPU=false
OCR_MAX_IMAGES=50
OCR_MAX_PIXELS=20000000
OCR_PDF_DPI=200
OCR_PDF_MIN_TEXT_LENGTH=40
```

Model bulunamadığında veya indirme kapalıyken model dizini hazır değilse API,
modelin nasıl hazırlanacağını belirten açık bir hata döndürür.

## Lokal AI Ayarları

Varsayılan mod dış servise bağlanmaz:

`backend/.env` içinde `AI_PROVIDER=local`

Gemma 4 E4B modelini Ollama ile kullanmak için:

```bash
ollama serve
ollama pull gemma4:e4b
```

`backend/.env` içinde:

```env
AI_PROVIDER=ollama
AI_ALLOW_REMOTE_SERVICES=false
OLLAMA_MODEL=gemma4:e4b
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_TIMEOUT=600
OLLAMA_PULL_TIMEOUT=3600
RAG_CHUNK_SIZE=1400
RAG_CHUNK_OVERLAP=220
RAG_TOP_K=6
```

Ollama varsayılan olarak `http://127.0.0.1:11434` adresinde çalışmalıdır. Uzak
servis ancak `AI_ALLOW_REMOTE_SERVICES=true` açık onayıyla kullanılabilir;
production uzak adresi HTTPS olmalı ve prompt/belge/görsel veri sınıflandırması
operasyon ekibi tarafından onaylanmalıdır.

Tam entegrasyon mimarisi, API sözleşmesi ve güvenlik notları için
[`docs/gemma4_ollama_architecture.md`](docs/gemma4_ollama_architecture.md) dosyasına bakın.

OpenAI uyumlu lokal bir Qwen servisine bağlanmak için:

```env
AI_PROVIDER=local_llm
LOCAL_LLM_BASE_URL=http://127.0.0.1:8001
LOCAL_LLM_MODEL=qwen2.5:14b
LOCAL_LLM_API_KEY=
LOCAL_LLM_TIMEOUT=180
```

Wrapper `POST /v1/chat/completions` endpoint'ini bekler.

## RAG ve Doküman Kontrolleri

Yükleme sırasında çıkarılan metin, çakışmalı ve sabit ofsetli parçalara ayrılır.
Parçalar içerik özeti (SHA-256), karakter aralığı ve belge içindeki sırasıyla
veritabanında saklanır. Sorgu sırasında Türkçe karakterleri destekleyen BM25
sıralaması en ilgili parçaları seçer; model yalnızca bu parçalarla ve belge içi
prompt injection talimatlarını uygulamaması istenerek çağrılır. Her kaynak
`D<doküman>-C<parça>` biçiminde kararlı bir kimlik taşır. Model kullanılamazsa
aynı kaynaklar yerel fallback yanıtında döndürülür.

Hazır sunucu kontrolleri çözümlenmemiş ifadeleri, izlenebilirlik kimliklerini ve
doğrulanabilir kabul kriterlerini inceler. Kullanıcılar Belge İşleme ekranından
kendi kontrol adını, açıklamasını, talimatını ve önem seviyesini ekleyebilir;
bu kayıtlar kullanıcı bazında izole edilir. Kontrol ve RAG çalıştırmaları sonuç,
kaynak ve zaman bilgileriyle `DocumentAnalysisRun` altında denetlenebilir biçimde
saklanır.

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
WHISPER_TIMEOUT=180
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

## IBM DOORS 9.7.0 Connector

`api.services.doors_connector.DoorsConnector`, aynı Windows oturumundaki IBM
DOORS 9.7.0 istemcisine manual'da tanımlı `DOORS.Application` OLE Automation
arayüzü üzerinden bağlanır. Sabit DXL köprüsü hiyerarşi, modül, öznitelik,
nesne ve link okuma/yazma işlemlerini kapsar; serbest DXL çalıştırmaz ve kalıcı
silme sunmaz.

Windows koşullu `pywin32` bağımlılığı `backend/requirements.txt` içindedir.
DOORS kurulum, güvenlik, kullanım, kabul testi ve mimari gerekçesi için
[`docs/doors_connector.md`](docs/doors_connector.md), manual perm izlenebilirliği
için [`docs/doors_manual_traceability.md`](docs/doors_manual_traceability.md)
dosyalarına bakın.

## Frontend

Frontend `.node-version` ile Node.js 24.19.x sürümünü ve lockfile ile npm paket
çözümünü sabitler.

```bash
cd frontend
npm ci
npm run dev
```

Frontend API proxy hedefi `frontend/.env` dosyasındaki `VITE_API_TARGET` değeriyle
belirlenir. Örnek için [`frontend/.env.example`](frontend/.env.example) dosyasına
bakın.

Varsayılan frontend adresi:

```text
http://localhost:5173
```

Frontend, geliştirme modunda Django API'ye `/api` proxy'si üzerinden bağlanır.

## Kalite kapıları

Backend:

```bash
backend/.venv/bin/python backend/manage.py check
backend/.venv/bin/python backend/manage.py makemigrations --check --dry-run
backend/.venv/bin/python backend/manage.py test api config --noinput
backend/.venv/bin/python -m ruff check launcher.py backend/config backend/api
backend/.venv/bin/python -m ruff format --check launcher.py backend/config backend/api
backend/.venv/bin/python -m mypy
backend/.venv/bin/python -m pip check
```

Frontend:

```bash
npm --prefix frontend run check
```

Production yapılandırmasını ayrıca güvenli environment değerleriyle
`manage.py check --deploy --fail-level WARNING` üzerinden doğrulayın. Tam
geliştirme ve güvenlik süreci
[`CONTRIBUTING.md`](CONTRIBUTING.md) ile [`SECURITY.md`](SECURITY.md) içindedir.
