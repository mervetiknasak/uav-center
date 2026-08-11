# RAG ve Doküman Analizi Mimarisi

## Veri akışı

1. `DocumentUploadView`, doğrulanmış dosya için kullanıcı sahipliğinde bekleyen bir
   `Document` ve kalıcı `AsyncJob` oluşturur; `202 Accepted` döner.
2. `run_job_worker`, işi atomik olarak claim eder ve extractor/OCR katmanıyla metni
   request sürecinden bağımsız çıkarır.
3. `index_document` metni çakışmalı parçalara böler ve `DocumentChunk` kayıtlarını
   atomik olarak yeniler.
4. `retrieve` sorguyu ve parçaları normalize ederek BM25 skoruyla en ilgili 1–12
   kaynağı seçer.
5. `answer_document_query` kaynakları `AIWrapper` üzerinden Ollama veya OpenAI
   uyumlu yerel modele gönderir.
6. Upload analizi `Document.ai_result`; sonradan çalıştırılan RAG/kontrol yanıtları
   ise kaynak ve sağlayıcı bilgisiyle `DocumentAnalysisRun` altında tutulur.

Liste, detay, silme, RAG, kontrol ve analiz geçmişi aynı görünür belge selector'ını
kullanır. Normal kullanıcı yalnız kendi belgesine; staff denetim amacıyla bütün
belgelere erişebilir. Sahibi belirlenemeyen eski kayıtlar yalnız staff'a görünür.

Harici vektör veritabanı zorunlu değildir. Bu, mevcut SQLite kurulumu ile deterministik ve ağdan bağımsız retrieval sağlar. Daha büyük koleksiyonlarda `retrieve` arabirimi korunarak PostgreSQL FTS/pgvector veya ayrı bir vektör deposu eklenebilir.

## Kontrol türleri

- `system`: Sunucuda kodla tanımlanan, sürümlenebilir ve bütün kullanıcılara açık kontroller.
- `custom`: Kullanıcının arayüzden oluşturduğu, yalnızca sahibinin görebildiği ve değiştirebildiği model destekli kontroller.

Boş bir `control_ids` dizisi gönderilirse bütün hazır kontroller ile kullanıcının aktif kontrolleri çalışır. Tek istekte en fazla 10 kontrol kabul edilir.

## Güvenlik ve dayanıklılık

- Model bağlamı yalnızca retrieval sonucundaki kaynaklarla sınırlandırılır.
- Sistem prompt'u belge içeriğini güvenilmeyen veri olarak işaretler ve belge içindeki komutların uygulanmasını yasaklar.
- Kullanıcı kontrollerinde sahiplik hem queryset hem çalıştırma anında doğrulanır.
- Kaynakların karakter ofseti ve SHA-256 özeti denetlenebilirlik sağlar.
- Model erişilemezse kullanıcıya kaynaksız bir tahmin verilmez; seçilmiş kaynak parçalarıyla yerel fallback döner.
- Parça boyutu, çakışma ve retrieval limiti ortam ayarlarıyla yönetilir.

## API örnekleri

```json
POST /api/documents/42/rag/query/
{"query": "Uçuşa elverişlilik riskleri neler?", "top_k": 6}
```

```json
POST /api/analysis-controls/
{
  "name": "Birim tutarlılığı",
  "description": "Sayısal değerlerde SI birimlerini inceler",
  "instructions": "Birim verilmeyen veya birbiriyle çelişen sayısal büyüklükleri bul.",
  "severity": "warning"
}
```

```json
POST /api/documents/42/controls/run/
{"control_ids": ["unresolved-markers", "custom:7"]}
```
