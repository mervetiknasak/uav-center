# UAV Center — Agent Mühendislik Rehberi

Bu dosya, repository üzerinde çalışan insan ve yazılım ajanları için bağlayıcı
mühendislik sözleşmesidir. Amacı yalnızca çalışan kod üretmek değil; güvenli,
test edilebilir, geriye uyumlu ve sürdürülebilir değişiklikler üretmektir.

## 1. Kapsam ve yorumlama

- Bu dosya repository kökünden itibaren tüm dosyalar için geçerlidir.
- Daha alt bir dizinde ayrıca `AGENTS.md` bulunursa, yalnızca o alt ağaç için daha
  özel olan talimatlar önceliklidir.
- Kullanıcının açık isteği, bu dosyadaki genel çalışma tercihlerinden önceliklidir;
  ancak güvenlik, veri bütünlüğü ve yetkilendirme kuralları sessizce aşılmaz.
- Bu belgede **ZORUNLU** ihlal edilmemesi gereken kuralı, **ÖNERİLİR** güçlü
  varsayılanı, **YASAK** ise açıkça yapılmaması gereken işlemi ifade eder.
- Çalışan kod ve sürümlenmiş yapılandırma gerçek durumun kaynağıdır. Bu belge ile
  kod çelişiyorsa tahmin yürütme; davranışı doğrula ve değişiklik kapsamındaysa
  belgeyi de güncelle.

## 2. Değişmez öncelikler

Kararlar şu sırayla optimize edilir:

1. Güvenlik, gizlilik ve veri bütünlüğü.
2. Doğru davranış ve açık hata yönetimi.
3. Mevcut API, veri ve kullanıcı deneyimiyle geriye uyumluluk.
4. Katman sınırları, test edilebilirlik ve bakım kolaylığı.
5. Performans ve kaynak kullanımı.
6. En küçük, anlaşılır ve geri alınabilir değişiklik.

Bir özellik talebi bu önceliklerden biriyle çelişiyorsa risk görünür kılınır;
sessiz varsayımla güvenlik veya veri bütünlüğünden ödün verilmez.

## 3. Projenin doğrulanmış teknik profili

| Alan | Mevcut teknoloji / sözleşme |
| --- | --- |
| Backend | Python 3.11, Django 5.2, Django REST Framework 3.18 |
| Frontend | Node.js 24.19.x, Vue 3 Composition API, JavaScript, Vite 6, Naive UI, Vue Router |
| Kimlik | Django session authentication + CSRF; aktif kullanıcı ve admin ayrımı |
| Veri | Geliştirmede SQLite, dosyalar `backend/media/` altında |
| Arka plan işleri | `AsyncJob` tabanlı kalıcı kuyruk ve `run_job_worker` |
| Yerel AI | Ollama/Gemma, OpenAI uyumlu yerel LLM ve lokal/HTTP Whisper sınırları |
| Belge işleme | PDF/DOCX/XLSX/PPTX/metin/görsel çıkarımı, opsiyonel EasyOCR |
| Retrieval | Kalıcı `DocumentChunk` kayıtları ve BM25 tabanlı grounded RAG |
| Kurumsal entegrasyon | Jira ve Windows'a özgü IBM DOORS 9.7 OLE/DXL köprüsü |
| Dil / saat | Kullanıcı metinleri ağırlıklı Türkçe; `Europe/Istanbul`, timezone-aware Django |

Proje local-first tasarlanmıştır. Varsayılan geliştirme ve test akışı gerçek bir
Jira, DOORS, SMTP, Ollama, Whisper servisi veya OCR model indirmesi gerektirmemelidir.

## 4. Repository haritası ve sahiplik sınırları

| Yol | Sorumluluk |
| --- | --- |
| `launcher.py` | Çapraz platform ortam hazırlama; backend, worker ve frontend süreçlerini başlatma |
| `backend/config/` | Django ayarları, ortam değişkenleri ve kök URL yapılandırması |
| `backend/api/<feature>/` | Feature'ın model, selector, serializer, application service, view ve URL bileşimi |
| `backend/api/common/` | Yalnız iki veya daha fazla feature'ın gerçekten paylaştığı dar altyapı |
| `backend/api/models.py` | Django discovery ve eski importlar için açık, ince model façade'ı |
| `backend/api/serializers.py`, `backend/api/views.py` | Açık compatibility façade'ları; yeni davranışın sahibi değildir |
| `backend/api/services/` | Belge/AI/RAG/job işleme ve dış sistem adaptörleri için kararlı servis yüzeyi |
| `backend/api/management/commands/` | Worker ve açıkça çağrılan operasyonel komutlar |
| `backend/api/migrations/` | İleri yönlü ve sıralı şema geçmişi |
| `backend/api/tests.py`, `backend/api/test_*.py` | Django/unittest tabanlı regresyon ve sözleşme testleri |
| `frontend/src/app/` | Composition root, uygulama context'i, shell ve navigasyon |
| `frontend/src/features/` | Route page, feature-owned model, composable ve bileşenler |
| `frontend/src/composables/`, `frontend/src/components/` | Kademeli taşıma yüzeyi ve gerçekten paylaşılan davranış/UI |
| `frontend/src/views/` | Kademeli taşıma sırasında korunan sunum façade'ları |
| `frontend/src/router/` | Lazy-loaded rotalar, menü eşlemesi ve admin UX korumaları |
| `docs/` | RAG, Ollama, Jira/DOORS gibi mimari ve operasyonel sözleşmeler |

Kök `models.py`, `serializers.py` ve `views.py` dosyaları Django discovery ve açık
uyumluluk importları dışında davranış içermez. `App.vue` yalnız provider, kimlik
shell'i ve `RouterView` bileşimidir. Yeni davranış feature paketine eklenir; façade
ve app shell yeniden birleştirme noktası olarak büyütülmez. Mevcut büyük rota
görünümleri dokunulan alan oranında feature composable/component sınırlarına
kademeli taşınır; yalnız satır sayısı için anlamsız parçalama yapılmaz.

Başlıca domain sınırları; kimlik/üyelik, belge-OCR-RAG, AI Studio, organizasyon,
teknik dokümanlar, uçuş izinleri, Word-to-Jira ve DOORS entegrasyonudur. Yeni bir
özellik önce bu sınırlardan hangisine ait olduğunu belirlemeli; farklı domain'ler
arasında doğrudan model/view bağımlılığı kurmak yerine açık bir application service
veya dar port kullanmalıdır.

İzin verilen yönlü bağımlılıklar: belge ingestion akışı `documents → jobs`, teknik
dokümanların organizasyon okuma modeli `technical_documents → organization` ve
toplantı sorumlu eşlemesi `meeting_minutes → organization` yönündedir. Bu yönler
tersine çevrilmez ve döngü oluşturmaz; yeni cross-feature erişim dar public API,
selector veya port üzerinden eklenir. Production kodu kök compatibility
`models.py`/`serializers.py`/`views.py` façade'larını import etmez.

## 5. Kanonik veri akışları

### 5.1 Standart HTTP isteği

1. Feature URL modülü kararlı rotayı tanımlar; `backend/api/urls.py` yalnız açık
   `include(...)` bileşimini yapar.
2. View kimlik, yetki, nesne görünürlüğü ve HTTP orkestrasyonunu uygular.
3. Serializer biçim, tip, alanlar arası kural ve güvenilmeyen girdiyi doğrular.
4. Birden fazla yerde kullanılabilen iş kuralı servis katmanında çalışır.
5. Model/veritabanı değişikliği gerekli atomiklik ve kısıtlarla yapılır.
6. Yanıt tutarlı serializer şekli ve anlamlı HTTP durum koduyla döner.

### 5.2 Belge yükleme ve asenkron işleme

`DocumentUploadView` → `DocumentUploadSerializer` → atomik `ingest_document` →
bekleyen `Document` + `AsyncJob` → `run_job_worker` → extractor/OCR → RAG
indeksleme → opsiyonel AI → sonuçların kalıcılaştırılması. Veritabanı rollback'i
dosya depolamasını otomatik geri almadığından ingestion servisi orphan dosyayı
compensating cleanup ile kaldırır.

Bu akışta istek OCR veya model yanıtını beklemez; kabul edilen iş için `202`
dönmeye devam eder. Job sahipliği, atomik claim, retry/backoff, stale recovery,
iptal yarışı ve durum geçişleri korunması gereken sözleşmelerdir.

### 5.3 Frontend isteği

View/component → özellik composable'ı → `useApi.apiFetch` → `/api` → Django.
Standart istekler session cookie ve CSRF yönetimini atlayarak doğrudan `fetch`
çağırmamalıdır. NDJSON akışlı Ollama sohbeti gibi streaming gerektiren istisnalar
mevcut `useOllama` desenini izlemeli; yine credentials, CSRF, hata ve iptal
yönetimini korumalıdır.

### 5.4 Dış sistem isteği

View veya serializer dış sağlayıcı SDK/HTTP/OLE çağrısı yapmaz. Çağrı, ayarları
`django.conf.settings` üzerinden alan servis/adaptör sınırından geçer; timeout,
TLS, veri dönüştürme ve sağlayıcı hatası burada ele alınır. HTTP katmanı iç hata
ayrıntılarını sızdırmadan uygun `4xx/5xx` yanıtına çevirir.

## 6. Mimari kurallar ve SOLID uygulaması

### Tek Sorumluluk — SRP

- Model kalıcılık ve veri bütünlüğünü; serializer doğrulama/temsil işini; view
  HTTP orkestrasyonunu; servis ise iş kuralını üstlenir.
- Vue view'ları sunuma odaklanır. API çağrısı, yükleme/hata durumu ve yeniden
  kullanılabilir davranış özellik composable'ında tutulur.
- Bir modülün değişmesi için birden fazla bağımsız neden oluşuyorsa bölme sınırı
  aranır. Yalnız satır sayısı için anlamsız dosya parçalama yapılmaz.

### Açık/Kapalı — OCP

- Yeni sağlayıcı, job türü, belge formatı veya kontrol tipi eklerken kararlı
  arabirim/registry genişletilir; büyüyen koşul zincirleri kopyalanmaz.
- Mevcut örnekler: `JOB_HANDLERS`, belge extractor uzantı kümeleri, AI wrapper ve
  DOORS transport protokolü.
- Genişletme noktası gerçekten ikinci bir uygulamaya sahip olmadan spekülatif
  framework veya soyut fabrika eklenmez.

### Liskov Yerine Geçme — LSP

- Aynı portu uygulayan sağlayıcılar aynı girdi anlamını, temel dönüş şeklini ve
  hata semantiğini korur.
- Bir adaptörün çağıranı, özel sağlayıcı tipini kontrol etmek zorunda kalıyorsa
  port sözleşmesi yeniden değerlendirilir.
- Fallback davranışı başarı gibi görünmemeli; provider/model bilgisi ve hata
  bağlamı mevcut sözleşmeye uygun şekilde görünür kalmalıdır.

### Arayüz Ayrımı — ISP

- Dış sistemler için geniş “her şeyi yapan” istemciyi tüm iş katmanına yayma.
  Kullanıcının ihtiyacı olan dar operasyonları servis fonksiyonları veya küçük
  `Protocol` sözleşmeleriyle sınırla.
- Test doubles yalnız kullanılan metotları uygulayabilmelidir.

### Bağımlılığın Tersine Çevrilmesi — DIP

- İş kuralları doğrudan `urllib`, Jira SDK, OLE nesnesi veya dosya sistemi
  ayrıntısına bağımlı olmamalı; bunlar adaptör sınırında kalmalıdır.
- Dış istemci/config nesneleri testte değiştirilebilir veya enjekte edilebilir
  olmalıdır. Global import sırasında ağ bağlantısı, model yükleme ya da pahalı
  kaynak oluşturma yapılmaz.
- Framework nesneleri domain fonksiyonlarına gereksizce taşınmaz; mümkünse sade,
  açık ve serialize edilebilir girdiler kullanılır.

### Basitlik ilkesi

- SOLID, gereksiz soyutlama üretmek için kullanılmaz. Önce mevcut desene uyan en
  küçük doğru çözüm uygulanır; tekrar veya değişim ekseni kanıtlandığında soyutlanır.
- Yeni Django app, global state yönetim kütüphanesi, UI framework veya kapsamlı
  katmanlaşma ancak gerçek bir domain sınırı ve açık gereksinim varsa eklenir.
- Özellik çalışması sırasında ilgisiz “temizlik” veya repository çapında yeniden
  adlandırma yapılmaz.

### Kod stili ve isimlendirme

- Python'da mevcut stil izlenir: 4 boşluk, `snake_case` fonksiyon/değişken,
  `PascalCase` sınıf ve büyük harfli sabitler. Tarih/saat için naive `datetime`
  yerine `django.utils.timezone` kullanılır.
- Dış sistem/config/veri taşıma sınırlarında type hint, `dataclass` ve gerektiğinde
  dar `Protocol` kullanımı **ÖNERİLİR**. Tip ipucu, belirsiz veya yanlış bir
  sözleşmeyi süslemek için eklenmez.
- Vue/JavaScript'te mevcut biçim korunur: 2 boşluk, çift tırnak, noktalı virgül,
  `<script setup>` ve açık isimli composable/event'ler.
- Değiştirilen Python ve frontend kaynakları repository formatter'ıyla biçimlenir;
  ilgisiz kullanıcı değişiklikleri sırf format için kapsama alınmaz. Public import
  veya test patch noktası taşınmadan önce tüm referanslar `rg` ile aranır;
  geriye uyumluluk shim'i gerekçesiz kaldırılmaz.

## 7. Backend mühendislik standartları

### 7.1 API ve doğrulama

- Tüm güvenilmeyen veri serializer veya açık bir domain doğrulayıcısından geçmek
  **ZORUNDADIR**. Yalnız frontend doğrulamasına güvenmek **YASAKTIR**.
- Alan uzunluğu, enum, dosya boyutu/türü, liste sınırı ve alanlar arası kurallar
  yan etkiden önce doğrulanır.
- Beklenen durum kodları korunur: oluşturma `201`, kuyruğa alma `202`, başarılı
  gövdesiz silme `204`, girdi `400`, kimlik/yetki `401/403`, görünmeyen nesne
  `404`, durum yarışı `409`, dış sağlayıcı `502`.
- Hatalar DRF alan hataları veya `{"detail": "..."}` biçiminde, kullanıcıya
  anlaşılır Türkçe mesajlarla döner. Stack trace, token, parola, dahili yol veya
  sağlayıcının hassas cevabı API'ye taşınmaz.
- Yeni/yenilenen endpoint için rota, serializer, view, frontend çağrısı, test ve
  README/dokümantasyon birlikte değerlendirilir.

### 7.2 Kimlik doğrulama ve nesne görünürlüğü

- Backend yetkilendirmesi tek otoritedir. Router'daki `requiresAdmin` yalnız UX
  korumasıdır ve backend izninin yerine geçmez.
- Aktif kullanıcı kontrollerinde mevcut `IsActiveAuthenticated`; admin yazma
  işlemlerinde `IsActiveAdminUser` veya alanın mevcut izin sınıfı kullanılır.
- Kullanıcıya ait kaynaklar queryset seviyesinde owner/creator ile filtrelenir;
  yalnız URL'den gelen kimliği kontrol etmek yeterli değildir.
- Repository karma bir görünürlük modeline sahiptir: belge owner-scoped'dur ve
  staff tüm belgeleri/analiz geçmişini denetleyebilir; job ve özel kontrol yalnız
  sahibine görünür. Uçuş izinleri ile bazı kurumsal kayıtlar rol tabanlı
  paylaşımlıdır. “Her kayıt owner-scoped” varsayımı yapma; her yeni kaynak için
  paylaşımlı mı kullanıcıya özel mi olduğunu açıkça belirle.
- Varlığını açıklamaması gereken başka kullanıcı kaydı için filtreli queryset ve
  `404` tercih edilir.
- Yeni bir endpoint eklerken anonim, pasif kullanıcı, aktif kullanıcı, başka
  kaydın sahibi ve admin senaryoları bilinçli biçimde kararlaştırılır ve test edilir.
- Mevcut bir kaynağın görünürlük modelini değiştirmek ayrı bir güvenlik/API kararıdır;
  özellik yan etkisi olarak sessizce yapılmaz.

### 7.3 İş kuralları ve yan etkiler

- View'lar ince kalır: doğrula, yetkilendir, servisi çağır, yanıtı dönüştür.
- Birden fazla endpoint/command/worker tarafından kullanılabilecek davranış
  ilgili feature'ın `services/` sınırında tutulur. Ortak belge/AI/RAG/job işleme
  veya dış adaptör yüzeyi gerekiyorsa `backend/api/services/` kullanılır.
- E-posta, dosya yazma, Jira/DOORS işlemi veya model çağrısı gibi yan etkiler açık
  isimli fonksiyonlarda görünür olmalı; model `save()` veya import sırasında
  şaşırtıcı biçimde tetiklenmemelidir.
- Dış çağrı veritabanı transaction'ını gereksiz yere açık tutmamalıdır. Önce veri
  hazırlanır, dış çağrı timeout ile yapılır, sonuç/audit ayrı ve güvenli adımda
  kalıcılaştırılır.

### 7.4 Veritabanı, transaction ve sorgular

- Birlikte başarı/başarısız olması gereken çoklu yazımlar `transaction.atomic`
  içine alınır. Eşzamanlı durum geçişlerinde compare-and-set güncelleme,
  `select_for_update` veya veritabanı kısıtı değerlendirilir.
- Benzersizlik ve değişmez veri kuralları yalnız uygulama koduna bırakılmaz;
  uygun `UniqueConstraint`, `CheckConstraint`, foreign key ve indeks kullanılır.
- Liste/detay sorgularında N+1 üretme; ilişkiye göre `select_related` ve
  `prefetch_related` kullan. Filtre/sıralama desenleri yeni indeks gerektiriyor mu
  değerlendir.
- Büyük queryset'i sebepsiz `list()` ile belleğe alma; sayfalama veya makul limit
  uygula. JSONField değerleri taşınabilir ve JSON-serialize edilebilir olmalıdır.
- Production eşzamanlılığı SQLite varsayımlarıyla tasarlanmaz. Çoklu worker
  semantiği satır düzeyinde kilitlemeyi destekleyen veritabanında da doğru olmalıdır.

### 7.5 Migration politikası

- Model değişikliği yeni migration ile birlikte teslim edilir.
- Paylaşılmış/eski migration dosyalarını düzenlemek, silmek veya yeniden
  numaralandırmak **YASAKTIR**. Düzeltme yeni ileri yönlü migration ile yapılır.
- Veri migration'ı deterministik, tekrar çalıştırmaya dayanıklı ve büyük veri için
  toplu/iteratif olmalıdır. Ağ veya dış servis çağırmamalıdır.
- Yıkıcı şema değişikliği önce expand/migrate/contract yaklaşımıyla geriye uyumlu
  planlanır; veri kaybı ihtimali kullanıcı onayı olmadan kabul edilmez.
- Her model değişikliğinde `makemigrations --check --dry-run` doğrulaması yapılır.

### 7.6 Job kuyruğu

- Yeni job türü açık payload şeması, handler kaydı, sahiplik, retry ve kalıcı sonuç
  davranışıyla eklenir.
- Handler aynı job yeniden çalıştığında veri bozmamalı veya dış sistemde mükerrer
  yan etki üretmemelidir. Gerekirse idempotency anahtarı/audit kaydı kullanılır.
- Claim işleminin atomikliği, `attempts`, `available_at`, `locked_at`, `locked_by`,
  cancellation ve stale recovery anlamları korunur.
- Hata mesajı teşhis edilebilir fakat sınırlı ve güvenlidir. İlerleme değeri
  `0..100` aralığında ve mantıksal olarak monoton olmalıdır.
- Uzun süren OCR/AI/dış sistem işi request thread'ine taşınmaz.

### 7.7 Dosya, OCR, AI ve RAG güvenliği

- Dosya uzantısı, boyutu, OOXML zorunlu parçaları, arşiv öğesi/açılmış boyut,
  piksel/sayfa/görsel sınırı ve çıkarılan metin uzunluğu sunucuda doğrulanır.
  Kullanıcı dosya adı güvenilir yol olarak kullanılmaz.
- Kalıcı kullanıcı dosyaları kontrollü storage/`MEDIA_ROOT` altında tutulur.
  Ephemeral dönüşüm dosyaları güvenli OS temp veya izinleri kısıtlı, açıkça
  yapılandırılmış temp dizininde oluşturulabilir; context/finally ile exception
  halinde de temizlenir ve kalıcı veri sayılmaz.
- OCR model indirme çalışma anında varsayılan olarak kapalı kalır. Test veya rutin
  doğrulama internetten model indirmemelidir.
- Belge ve kullanıcı prompt'u güvenilmeyen veridir. Prompt injection talimatı
  sistem kuralı olarak uygulanmaz; RAG bağlamı seçilmiş kaynaklarla sınırlandırılır.
- `DocumentChunk` konumları, karakter ofsetleri, hash'leri ve kaynak kimlikleri
  denetlenebilirlik sözleşmesidir. Retrieval değişikliği kaynaklılık testlerini
  korumalıdır.
- Model yokken fallback, model üretmiş gibi iddia sunmamalı; provider bilgisi ve
  seçilmiş kaynaklar açık kalmalıdır.
- Görsel/base64, belge metni ve model cevabı gereksiz loglanmaz veya yeni bir dış
  servise açık onay olmadan gönderilmez.
- AI servisleri varsayılan olarak loopback/private hostlarla sınırlıdır. Uzak AI
  erişimi açık `AI_ALLOW_REMOTE_SERVICES=true` onayı gerektirir; production'da
  HTTPS ve belge/prompt/görsel veri sınıflandırması incelemesi zorunludur.
- Belge hücresi/metni, e-posta veya başka PII için geçici `print` bırakmak
  **YASAKTIR**; gerekli teşhis, redakte edilmiş ve seviyelendirilmiş logger ile yapılır.

### 7.8 Kurumsal entegrasyonlar

- Jira, DOORS, Ollama ve Whisper çağrılarında timeout zorunludur; TLS doğrulaması
  güvenli varsayılan olarak korunur.
- Sağlayıcıya özgü hata, ilgili custom exception ile normalize edilir ve HTTP
  sınırında kontrollü yanıta çevrilir.
- Jira yazmaları testte mock'lanır. Mükerrerliği önleyen meeting/action etiketleri
  ve tekrar deneme semantiği bozulmaz.
- E-posta gibi tekrarlandığında dış yan etki üreten HTTP işlemleri kalıcı,
  benzersiz idempotency anahtarıyla claim edilir; aynı anahtar farklı payload için
  `409` üretir ve bilinçli tekrar yeni anahtar kullanır. SMTP gönderimi ile audit
  commit'i arasındaki kesintide zaman aşan `pending` kayıt `unknown` olur; otomatik
  yeniden gönderilmez ve operatör uzlaştırması gerektirir.
- DOORS yalnız desteklenen Windows/OLE ortamında gerçek kabul testi görür. Serbest
  DXL çalıştırma veya kalıcı silme eklemek **YASAKTIR**. DXL köprüsü değişirse
  `docs/doors_connector.md` ve `docs/doors_manual_traceability.md` izleri güncellenir.
- Tarayıcı Ollama'ya doğrudan bağlanmaz. Model pull/unload admin sınırında; araç
  çağrıları allow-list ve ayrı yetki olmadan otomatik yürütülmez.

## 8. Frontend mühendislik standartları

- Composition API ve mevcut JavaScript yaklaşımı korunur. Kısmi TypeScript geçişi,
  yeni state framework'ü veya ikinci UI kütüphanesi kapsam dışı yan etki olarak
  eklenmez.
- Naive UI, Lucide ve `styles/` altındaki mevcut tasarım modülleri yeniden
  kullanılır. Kök `style.css` yalnız sıralı composition façade'ıdır; feature stili
  ait olduğu modüle eklenir ve aynı bileşenin ikinci bir görsel/desen uygulaması
  oluşturulmaz.
- Yeni global `n-*` bileşeni kullanımı `frontend/src/app/ui.js` registry'sine
  eklenir; registry–template eşleşme testi gereksiz tam Naive UI importunu engeller.
- View; form, tablo ve event bağlama işini yapar. API erişimi, yükleme/hata durumu,
  polling ve özellik iş kuralları composable'da tutulur.
- Paylaşılan HTTP davranışı `useApi` üzerinden geçer. Session için
  `credentials: "include"`, güvenli olmayan metotlar için CSRF korunur.
- Reaktif state doğrudan prop üzerinden değiştirilmez. Props aşağı, eventler
  yukarı akar; türetilmiş değer için `computed`, yan etki için kontrollü `watch`
  kullanılır.
- Her async kullanıcı işleminde loading durumu ve `finally` ile geri dönüş,
  anlamlı hata mesajı, gerekiyorsa tekrar deneme/iptal davranışı bulunur.
- Router'a yeni ekran eklenirse lazy import, kararlı route name, `menuKey`, menü
  bölümü ve admin meta bilgisi birlikte eklenir. Route page kendi feature
  composable/controller'ını kurar; veri/event bağlantısı `App.vue` içine taşınmaz.
- Route guard güvenlik sınırı değildir; API her zaman kendi iznini uygular.
- Backend'in snake_case API alanları sözleşmedir. Frontend içinde camelCase
  kullanılabilir; dönüşüm tek ve açık bir sınırda yapılır, rastgele karıştırılmaz.
- Kullanıcıya görünen yeni metin mevcut ürün diliyle uyumlu Türkçe; kod
  tanımlayıcıları anlaşılır İngilizce olmalıdır.
- Büyük görünüm dosyasına bağımsız yeni panel eklerken dar bir component çıkarma
  değerlendirilir. Ancak mevcut ekranlar özellik çalışması bahanesiyle topluca
  yeniden yazılmaz.
- Production build bugün büyük ana chunk uyarısı verebilir. Bu mevcut uyarıyı test
  hatası gibi sunma; fakat yeni ağır bağımlılıkla boyutu gereksiz büyütme, route
  lazy-loading'i koru ve anlamlı bundle artışını teslim notunda belirt.
- Klavye erişimi, buton etiketi/tooltip'i, form label'ı, boş-yükleniyor-hata
  durumları ve dar ekran davranışı kullanıcı kabulünün parçasıdır.

## 9. Test politikası

### 9.1 Temel ilkeler

- Her bug fix önce hatayı gösteren veya aynı regresyonu yakalayan test içerir.
- Yeni davranış en az başarı, doğrulama hatası ve ilgili yetki/sağlayıcı hatası
  senaryolarını kapsar.
- Saf davranış için `SimpleTestCase`/`unittest.TestCase`; veritabanı/API için
  `TestCase` veya `APITestCase` kullanılır.
- Dosya testlerinde geçici dizin ve `override_settings(MEDIA_ROOT=...)` kullanılır;
  gerçek `backend/media/` kirletilmez.
- Ağ, e-posta, OCR reader/model, Jira SDK, Ollama/Whisper ve OLE sınırları mock/fake
  edilir. Varsayılan test suite'i gerçek dış sisteme veya internete çıkmaz.
- Mock, yalnız işbirliği sınırında yapılır; test edilen iş kuralını mock'lamak
  **YASAKTIR**.
- Zaman, sıra, retry ve kaynak kimliği testleri deterministik olmalıdır. Testler
  birbirinin oluşturduğu veriye veya çalışma sırasına güvenmez.
- Sadece yeni testin geçmesi yeterli değildir; ilgili modül testi ve teslimden önce
  makul olduğu ölçüde tüm backend suite'i çalıştırılır.

### 9.2 Değişiklik türüne göre asgari doğrulama

| Değişiklik | Asgari doğrulama |
| --- | --- |
| Saf backend servis/fix | İlgili test modülü + `manage.py check` |
| API/serializer/permission | İlgili API testleri + tam `manage.py test api` |
| Model veya sorgu | İlgili testler + migration check + tam backend suite |
| Job/worker | Başarı, retry, terminal hata, sahiplik/iptal testi + tam suite |
| OCR/AI/Jira/DOORS | Mock'lu unit/contract testleri; gerçek servis otomatik çağrılmaz |
| Frontend model/composable | İlgili Vitest testi + `npm run lint` |
| Frontend JS/Vue/CSS | `npm run check` + etkilenen ekran için manuel smoke notu |
| Rota veya API sözleşmesi | Backend testleri + frontend build + uçtan uca manuel akış |
| Yalnız doküman | Link, yol ve komutların kod/config ile karşılaştırılması |

Repository Ruff, kademeli mypy, ESLint, Prettier ve Vitest kullanır. Kesin kapsam ve
istisnaların kaynağı `pyproject.toml`, frontend config'leri ve package script'leridir;
migration'lar formatter/lint/type kapsamı dışında, mypy ise kademeli ve global
strict değildir. Kalite kapısını yeni hata gizlemek için daraltma.
`.github/workflows/ci.yml` yerel kapıları pull request ve ana branch push'unda
tekrarlar. `security.yml` ağ gerektiren dependency audit'lerini ayrı çalıştırır;
yerel test sonucunu “CI geçti” diye raporlama.

## 10. Kanonik komutlar

Komutlar aksi belirtilmedikçe repository kökünden çalıştırılır.

### 10.1 Kurulum ve geliştirme

```bash
# Python 3.11, backend venv, npm paketleri, migration, backend, worker ve frontend
python3 launcher.py

# İhtiyaca göre tek taraf
python3 launcher.py --backend-only
python3 launcher.py --frontend-only
python3 launcher.py --skip-install
python3 launcher.py --job-workers 4
```

Launcher uzun süre çalışan süreçler başlatır ve migration uygular. Yalnız statik
doğrulama gereken işte gereksiz yere çalıştırılmaz.

Manuel temiz kurulum:

```bash
python3.11 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.txt -r backend/requirements-dev.txt
npm --prefix frontend ci
```

`requirements.txt` OCR/Whisper dahil tam runtime'ı kurar. AI inference gerektirmeyen
backend kalite ortamı için CI gibi `requirements-base.txt` +
`requirements-dev.txt` kullanılabilir. Python bağımlılıkları platformlar arası
hash-lock değildir; release build'inin çözümlenmiş artifact'i saklanır ve audit edilir.

Windows'ta Python yolu `backend\.venv\Scripts\python.exe`; launcher komutu
kuruluma göre `py launcher.py` veya `python launcher.py` olabilir.

### 10.2 Backend kalite kapıları

```bash
backend/.venv/bin/python -m ruff check launcher.py backend/config backend/api
backend/.venv/bin/python -m ruff format --check launcher.py backend/config backend/api
backend/.venv/bin/python -m mypy
backend/.venv/bin/python backend/manage.py check
backend/.venv/bin/python backend/manage.py makemigrations --check --dry-run
backend/.venv/bin/python backend/manage.py test api config --noinput
backend/.venv/bin/python -m pip check
```

Hedefli test örnekleri:

```bash
backend/.venv/bin/python backend/manage.py test api.test_rag
backend/.venv/bin/python backend/manage.py test api.test_jobs.AsyncJobApiTests
backend/.venv/bin/python backend/manage.py test api.tests.AuthApiTests
```

### 10.3 Migration ve operasyonel komutlar

```bash
backend/.venv/bin/python backend/manage.py makemigrations api
backend/.venv/bin/python backend/manage.py migrate
backend/.venv/bin/python backend/manage.py run_job_worker --once
backend/.venv/bin/python backend/manage.py seed_technical_documents
```

`migrate`, worker ve seed kalıcı yerel durumu değiştirebilir. Bunlar yalnız görev
gerektiriyorsa ve hedef veritabanı anlaşıldıysa çalıştırılır; test yerine kullanılmaz.

### 10.4 Frontend kalite kapısı

```bash
npm --prefix frontend ci
npm --prefix frontend run check
npm --prefix frontend run dev
```

`npm ci` bağımlılık kurulumu içindir; her küçük değişiklikte tekrarlanmaz. Paket
değişirse `package.json` ile `package-lock.json` birlikte güncellenir. `check`;
lint, tüm frontend kaynaklarının format kontrolü, birim testleri ve production
build'i birlikte çalıştırır.

## 11. Değişiklik çalışma akışı

### Başlamadan önce

1. `git status --short` ile kullanıcı değişikliklerini belirle ve koru.
2. Bu dosyayı, ilgili README/docs bölümünü, hedef kodu ve en yakın testleri oku.
3. Etkilenen API, model, migration, izin, job, UI ve dış servis sözleşmelerini çıkar.
4. Belirsizlik güvenlik, veri kaybı, public API veya gerçek dış sistem yan etkisini
   etkiliyorsa uygulamadan önce netleştir.

### Uygularken

1. Mevcut desene uyan en küçük dikey dilimi değiştir.
2. İş kuralını doğru katmana koy; kopyala-yapıştır akışı üretme.
3. Başarı kodundan önce sınır, hata, yarış ve yetki durumlarını tasarla.
4. Regresyon testini değişiklikle birlikte ekle.
5. Yapılandırma, endpoint veya operasyon değiştiyse dokümanı aynı değişiklikte güncelle.

### Doğrularken

1. En dar ilgili testi önce çalıştır ve hızlı geri bildirim al.
2. Migration check, Django check ve frontend build gibi etkilenen kapıları çalıştır.
3. Ardından kapsamla orantılı tam suite'i çalıştır.
4. Komut çalıştırılamadıysa nedenini ve çalıştırılmayan doğrulamayı açıkça raporla;
   “geçti” izlenimi verme.
5. Son `git diff --check`, `git diff --stat` ve `git status --short` ile yalnız
   amaçlanan dosyaların değiştiğini doğrula.

### Teslim ederken

- Sonuçla başla; değişen davranışı ve önemli tasarım kararını kısaca açıkla.
- Çalıştırılan test/kapıları ve sonuçlarını belirt.
- Kalan risk, manuel kabul testi veya dış sistem doğrulaması varsa açıkça yaz.
- Kullanıcı istemedikçe commit, push, branch, PR veya deployment yapma.

## 12. Güvenlik, sırlar ve mahremiyet

- `.env` dosyaları, API tokenları, parolalar, cookie/session değerleri ve kurum içi
  URL'ler commit edilmez, çıktıda paylaşılmaz ve loglanmaz.
- Ayar isimleri `backend/config/settings.py` üzerinden yönetilir. Servis içinde
  dağınık `os.getenv` kullanımı yerine merkezi settings/config nesnesi tercih edilir.
- Dev varsayılanı olan secret/debug ayarları production güvenli sayılmaz. Production
  için güçlü secret, `DEBUG=false`, sınırlı host/origin, TLS ve uygun veritabanı gerekir.
- Production, gerçek teslimat yapmayan console/dummy/file/locmem e-posta
  backend'leriyle başlatılmaz; onaylı SMTP veya kurumsal delivery backend'i açıkça
  yapılandırılır.
- CSRF, session cookie, CORS ve TLS doğrulamasını “lokalde kolaylık” gerekçesiyle
  gevşetme. Güvensiz seçenek gerekiyorsa yalnız açık, belgeli dev kapsamına alınır.
- E-posta alıcıları BCC ile korunur; PII, belge metni ve model girdileri gereksiz
  telemetry/log alanına taşınmaz.
- Dosya indirmelerinde güvenli dosya adı, doğru content type ve
  `X-Content-Type-Options: nosniff` deseni korunur.
- Yeni bağımlılık lisans, bakım, güvenlik ve gerçekten ihtiyaç değerlendirmesi
  yapılmadan eklenmez. Sürüm aralığı mevcut dosyanın biçimiyle uyumlu tutulur.

## 13. Gözlemlenebilirlik ve hata yönetimi

- Beklenmeyen backend hataları kararlı event/request/resource kimliğiyle kaydedilir;
  kullanıcı yanıtı genel ve güvenli tutulur. Exception metni dış sağlayıcı, dosya
  yolu veya kullanıcı verisi içerebiliyorsa raw stack/message loglamak yerine ortak
  redaction sınırı ve güvenli structured `logger.error` kullanılır.
- Beklenen doğrulama/domain hataları exception stack'iyle log spam üretmez.
- Job ve dış sistem akışında kararlı kimlikler loglanabilir; token, belge içeriği,
  base64 görsel, parola veya tam PII loglanmaz.
- Hata yutmak **YASAKTIR**. Fallback varsa sonucu ve provider durumunu açıkça
  işaretler; yoksa kontrollü hata yükseltir.
- Yeni kritik akış; başarı, başarısızlık, süre/ilerleme ve audit ihtiyacını tasarımın
  parçası olarak ele alır.

## 14. Dokümantasyon ve sözleşme yönetimi

- `README.md` geliştirici kurulumu ve kullanıcıya açık genel yeteneklerin kaynağıdır.
- RAG/Ollama değişiklikleri ilgili `docs/*architecture.md`; DOORS değişiklikleri
  connector ve manual traceability belgeleriyle birlikte güncellenir.
- Yeni ortam değişkeni; adı, güvenli varsayılanı, örnek değeri ve etkisiyle belgelenir.
- Dokümanlarda makineye özgü mutlak yol yerine repository-relative bağlantı kullanılır.
- Public API alanı kaldırılmaz veya anlamı sessizce değiştirilmez. Gerekirse
  uyumluluk alanı/deprecation ve frontend geçişi aynı plan içinde yapılır.
- Mimari karar; yeni provider, database, framework, queue altyapısı veya güven sınırı
  getiriyorsa kısa bir mimari belge/karar notu eklenmesi **ÖNERİLİR**.

## 15. Git ve çalışma alanı disiplini

- Kullanıcının staged, unstaged ve untracked dosyaları kendisine aittir. İlgisiz
  değişiklikleri silme, geri alma, formatlama veya commit'e katma.
- `git reset --hard`, zorla checkout, rebase, amend, force-push ve geniş kapsamlı
  silme açık talep olmadan **YASAKTIR**.
- Generated/runtime içerikleri commit etme: `.env`, `.venv`, `node_modules/`,
  `frontend/dist/`, `db.sqlite3`, `backend/media/`, `backend/ocr_models/`, cache ve
  geçici Office kilit dosyaları.
- Commit istenirse repository geçmişine uygun kısa, emir kipinde İngilizce başlık
  kullan; bir commit tek mantıksal değişiklik taşısın.
- Binary Word şablonu (`flight_permit_template.docx`) yalnız görev açıkça
  gerektiriyorsa değiştirilir; üretilen belgenin alanları ve render sonucu ayrıca
  doğrulanır.

## 16. Önceden onay gerektiren durumlar

Aşağıdakiler kullanıcı isteğinin açık parçası değilse dur ve onay al:

- Veri kaybettirebilecek migration, kayıt/dosya silme veya local veritabanını sıfırlama.
- Gerçek Jira/DOORS/SMTP/Whisper/Ollama yazma işlemi, model indirme veya kurum dışına
  belge/görsel/metin gönderme.
- Public API'de kırıcı değişiklik veya mevcut yetki/görünürlük modelini değiştirme.
- Major dependency/framework yükseltmesi, yeni altyapı servisi veya UI/state
  framework'ü ekleme.
- Kullanıcıya ait binary şablonun, fixture'ın veya geniş üretilmiş içeriğin üzerine yazma.

## 17. Definition of Done

Bir değişiklik ancak aşağıdakiler sağlandığında tamamlanmış kabul edilir:

- [ ] İstenen davranış ve kapsam dışı bırakılanlar nettir.
- [ ] Kod doğru katmanda ve mevcut mimariyle uyumludur.
- [ ] Kimlik, yetki, sahiplik, CSRF ve hassas veri etkileri incelenmiştir.
- [ ] Girdi sınırları, hata yolları ve dış servis timeout/fallback davranışı ele alınmıştır.
- [ ] Veri değiştiyse kısıt, transaction, sorgu maliyeti ve migration hazırlanmıştır.
- [ ] Yeni davranış/regresyon için deterministik test eklenmiş veya gerekçesi yazılmıştır.
- [ ] İlgili hedefli testler ve kalite kapıları geçmiştir.
- [ ] Frontend değiştiyse production build ve manuel ekran akışı doğrulanmıştır.
- [ ] README/docs/config örnekleri davranışla senkronizedir.
- [ ] Secret, runtime dosyası, gereksiz binary veya ilgisiz kullanıcı değişikliği eklenmemiştir.
- [ ] Son diff küçük, anlaşılır, whitespace hatasız ve teslim özeti doğrulanabilirdir.
