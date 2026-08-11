# Gemma 4 + Ollama entegrasyon mimarisi

## Genel bakış

```text
Vue 3 / Gemma 4 Studio
  ├─ oturum + CSRF
  ├─ metin / görsel / sistem prompt'u
  ├─ örnekleme, bağlam, düşünme, JSON ve araç ayarları
  └─ NDJSON akış tüketicisi
            │
            ▼
Django REST API (/api/ai/ollama/*)
  ├─ IsActiveAuthenticated / IsActiveAdminUser
  ├─ istek boyutu ve alan doğrulama
  ├─ OllamaChatRequestSerializer
  └─ StreamingHttpResponse
            │ yalnızca localhost
            ▼
OllamaService (urllib tabanlı gateway)
  ├─ /api/version, /api/tags, /api/ps
  ├─ /api/pull, /api/generate (unload)
  └─ /api/chat (stream)
            │
            ▼
gemma4:e4b (Q4_K_M, 128K context, text + image)
```

Tarayıcı Ollama'ya doğrudan bağlanmaz. Kimlik doğrulama, CSRF koruması, istek
doğrulama ve model yönetimi yetkileri Django sınırında uygulanır. Bu tasarım,
Ollama'nın yalnızca `127.0.0.1:11434` üzerinde kalmasını ve uygulamanın ileride
başka bir yerel model sağlayıcısına geçirilebilmesini sağlar.

## Kurulum

Ollama'yı başlatın ve modeli indirin:

```bash
ollama serve
ollama pull gemma4:e4b
```

`backend/.env` için önerilen yapılandırma:

```env
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=gemma4:e4b
OLLAMA_TIMEOUT=600
OLLAMA_PULL_TIMEOUT=3600
```

Ardından uygulamayı `python3 launcher.py` ile başlatın ve **Araçlar → Gemma 4
Studio** sayfasını açın. Admin kullanıcıları eksik modeli bu sayfadan da
indirebilir ve bellekteki modeli boşaltabilir.

## API sözleşmesi

- `GET /api/ai/ollama/status/`: Ollama sürümü, kurulu ve çalışan modeller,
  yapılandırılmış model ve önerilen örnekleme değerleri.
- `POST /api/ai/ollama/pull/`: yapılandırılmış modeli indirir; yalnızca admin.
- `POST /api/ai/ollama/unload/`: modeli çalışma belleğinden çıkarır; yalnızca admin.
- `POST /api/ai/ollama/chat/`: `application/x-ndjson` akışlı sohbet üretir.

Sohbet ucu çok turlu geçmişi, sistem prompt'unu, en fazla üç base64 görseli,
düşünme çıktısını, `json` yanıt biçimini, Ollama araç tanımlarını, seed,
temperature, top-p, top-k, 128K'ya kadar bağlam, çıktı token sınırı ve keep-alive
ayarını destekler.

## İşletim ve güvenlik

- Model indirme ve bellekten çıkarma maliyetli işlemler olduğundan admin rolüyle
  sınırlandırılmıştır; aktif kullanıcılar modeli kullanabilir.
- Görseller için toplam istek sınırı ve üç görsel sınırı uygulanır. Görsel base64
  verisi sunucuda saklanmaz.
- Araç çağrıları test arayüzünde görünür fakat otomatik çalıştırılmaz. Gerçek araç
  yürütme eklenecekse fonksiyonlar sunucu tarafında açık allow-list, bağımsız
  yetkilendirme ve zaman aşımı ile uygulanmalıdır.
- Üretim ölçümleri (giriş/çıkış token sayısı, süre ve token/sn) yanıtın son NDJSON
  parçasından arayüzde gösterilir.
- Reverse proxy kullanılıyorsa `/api/ai/ollama/chat/` için buffering kapatılmalıdır;
  backend `X-Accel-Buffering: no` başlığını da gönderir.

## Genişletme noktaları

Kalıcı konuşmalar için mesajlar ayrı bir Django modeline yazılabilir. RAG eklemek
için belge parçalama/embedding/retrieval katmanı sohbet isteğinden önce bağlam
mesajı üretebilir. Gerçek agent döngüsü için modelin `tool_calls` çıktısı sunucuda
allow-list araç yürütücüsüne verilip `tool` rolüyle aynı konuşmaya eklenmelidir.
