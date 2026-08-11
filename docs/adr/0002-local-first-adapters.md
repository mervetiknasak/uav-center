# ADR-0002: Local-first dış sistem adaptörleri

- Durum: Kabul edildi
- Tarih: 2026-08-11

## Bağlam

UAV Center hassas belge, görsel, toplantı ve mühendislik verisi işler. Ollama,
Whisper, Jira, SMTP ve DOORS farklı güven/çalışma sınırlarına sahiptir.

## Karar

Varsayılan işleme yereldir. Tarayıcı dış sağlayıcıya doğrudan bağlanmaz. Use-case'ler
dar portlara; HTTP/OLE/SDK ayrıntısı timeout, TLS ve normalize hata sağlayan
adaptörlere bağımlıdır. Gerçek dış çağrılar varsayılan test suite'inde fake/mock ile
değiştirilir.

AI endpoint'leri varsayılan olarak loopback/private hostlarla sınırlandırılır.
Uzak AI için açık opt-in gerekir ve production uzak URL'si HTTPS olmak zorundadır.
Teknik doküman e-postası, request-scoped `Idempotency-Key` değerini document ile
birlikte benzersiz DB claim'i olarak yazar; aynı istek retry edildiğinde yeniden
göndermez, farklı payload aynı anahtarla gelirse `409` üretir. SMTP mutlak
exactly-once sağlamadığından gönderim ile başarı commit'i arasında kesilen ve
zaman aşan claim `unknown` durumuna alınır; otomatik replay yerine operatör
uzlaştırması istenir.

## Sonuçlar

- Belge verisinin istemeden buluta çıkması önlenir.
- Sağlayıcı değişimi domain/use-case kodunu etkilemez.
- Adaptör başına contract ve gerçek ortam kabul testi gerekir.
- Dış yan etkiler özel izin, audit ve idempotency gerektirir.
