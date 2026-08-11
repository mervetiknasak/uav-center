# ADR-0003: Kalıcı veritabanı job kuyruğu

- Durum: Kabul edildi
- Tarih: 2026-08-11

## Bağlam

OCR, belge çıkarımı ve AI analizi HTTP request süresinden uzun sürebilir. İşlerin
process restart'ında kaybolmaması, sahiplik, retry ve audit gerekir.

## Karar

İşler `AsyncJob` ile veritabanında tutulur. Worker compare-and-set claim, retry
backoff, stale recovery, progress ve terminal durum yönetimi uygular. Handler'lar
idempotent tasarlanır; kullanıcı yalnız kendi job'larını görür.

## Sonuçlar

- Broker olmadan yerel kurulum basit kalır.
- İş durumu ve hata denetlenebilir olur.
- Yüksek paralellikte SQLite yeterli değildir; üretimde satır düzeyinde
  eşzamanlılığı güçlü bir veritabanı gerekir.
- Kuyruk hacmi/latency ayrı broker gerektirecek düzeye ulaşırsa aynı job sözleşmesi
  korunarak adaptör değiştirilebilir.

