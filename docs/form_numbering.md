# Formlar–Numaratör entegrasyonu

Formlar → Ayarlar ekranında aktif yöneticiler bir FM şablonunun kayıt numarasını
veya metin alanını Numaratör formatıyla eşleştirir. Aynı hedef için tek eşleştirme
bulunur. Format seçilince her context key için form alanı, sabit değer, kullanıcı
girişi veya formatın sağladığı varsayılan seçilir. Tablo ve çoklu seçimler context
kaynağı değildir; hedef alanlar metin/uzun metin ve kayıt numarasıdır. Döngüsel
bağımlılıklar reddedilir.

## Kurulum

Yeni migration'ı normal deployment akışında uygulayın:

```sh
backend/.venv/bin/python backend/manage.py migrate
```

Merkezi Django ayarları:

| Değişken | Varsayılan | Anlamı |
| --- | --- | --- |
| `NUMARATOR_BASE_URL` | boş | Servis kökü; örneğin yerelde `http://127.0.0.1:8100`. `/api/private/v1/` otomatik eklenir. |
| `NUMARATOR_API_KEY` | boş | `formats:read` ve `numbers:generate` kapsamları bulunan, izinli formatlarla sınırlandırılmış sunucu anahtarı. |
| `NUMARATOR_TIMEOUT` | `15` | Her dış isteğin timeout'u, 1–120 saniye. |

Production'da HTTPS zorunludur. Uzak HTTP adresleri geliştirmede de kabul edilmez;
localhost/private ağ geliştirme adresleri HTTP kullanabilir. TLS doğrulaması
kapatılmaz, HTTP yönlendirmeleri izlenmez. Anahtar tarayıcıya veya loga gönderilmez.
Varsayılan boş ayarlar mevcut manuel form akışını etkilemez. Gerçek API anahtarı
kaynak koda eklenmemelidir.

## Numara alma

Formdaki hedefin yanındaki **Numara al** düğmesi, context değerlerini ve kaydetme
bilgisini gösterir. Gerekli context ile kayıt başlığı doldurulmalıdır. Hedef kayıt
numarası değilse manuel kayıt numarası da gereklidir. Dolu hedef üzerine yazılmaz.
Numara alınması yeni formu taslak olarak kaydeder, mevcut formun durumunu korur.
Dosya eki aynı istekte doğrulanıp saklanır. Arşivlenmiş formda numara alınamaz.

Üretim sonucundaki metin aynen saklanır. Numara ve üretimde kullanılan form alanları
backend tarafından kilitlenir. Formu sonradan düzenlemek veya eşleştirmeyi kapatmak
kilitleri kaldırmaz. Diğer form alanları düzenlenebilir. Yeni API alanları
`locked_fields` ve `numbering` mevcut form yanıtlarına eklenir; alan yolları
`record_number`, `title` veya `data.<alan_anahtarı>` biçimindedir.

## HTTP sözleşmesi

Tüm endpointler session authentication ve CSRF kullanır. Kök:
`/api/form-processes/numbering/`.

| İşlem | Yetki |
| --- | --- |
| `GET formats/?page=1` | Aktif admin; yanıt `results`, `page`, `total_pages`. Her sayfa en fazla 100 format. |
| `GET mappings/` | Aktif kullanıcı; normal kullanıcıya yalnız etkin eşleştirmeler. `template_code` ile filtrelenebilir. |
| `POST mappings/`, `PATCH mappings/<id>/` | Aktif admin. |
| `GET mappings/<id>/` | Aktif kullanıcı. |
| `POST allocations/` | Aktif kullanıcı; `Idempotency-Key` zorunlu. |
| `GET allocations/<uuid>/` | Formu mevcutsa paylaşımlı; henüz kaydedilmemiş/silinmişse işlemi başlatan veya admin. |
| `POST allocations/<uuid>/retry/` | İşlemi başlatan veya admin; gövdesiz, saklanan istekle devam eder. |

Eşleştirme alanları: `template_code`, `target_field`, `format_code`, `enabled`,
`context_sources`. Kaynak örnekleri: `{"source":"field","field":"data.program"}`,
`{"source":"fixed","value":"UAV"}`, `{"source":"manual"}`, `{"source":"default"}`.
`context_sources`, context key ile kaynak nesnesini eşler. `format_snapshot` ve
`updated_at` salt okunurdur. Mevcut eşleştirmenin form/hedef kimliği değiştirilemez.

Üretim isteği `mapping_id`, opsiyonel `record_id`, mevcut kayıtta zorunlu
`expected_updated_at`, `form` ve `manual_context` içerir. `form`; `template_code`,
`record_number`, `title`, `data`, `notes`, opsiyonel `remove_attachment` içerir.
Dosyalı istekte aynı JSON `payload` multipart alanında, dosya `attachment` alanında
iletilir. İlk başarılı yanıt `201`, tekrar `200`; `id`, `status`, `target_field`,
`document_number`, `record` döner. Doğrulama `400`, çakışma `409`, sağlayıcı/yerel
kurtarılabilir hata `502` olur. Oluşturulmuş işlem hatalarında `allocation_id` döner.

## Kalıcılık, tekrar deneme ve operasyon

`FormNumberMapping` yapılandırmayı; `FormNumberAllocation` değişmez istek,
context/alan anlık görüntüsü, aktör ve sağlayıcı sonucunu saklar. Şablon bazlı kilit
satırı eşzamanlı ayar güncellemelerinde bağımlılık grafiğini korur. Üretim önizlemesi
sıra tüketmeden hedef uzunluğunu denetler; gerçek sonuç yeniden denetlenir.

İşlem ağ çağrısından önce `pending` olarak kalıcılaştırılır. Başarılı sağlayıcı
sonucu `issued`, atomik form kaydı `completed` durumudur. Bir lease aynı işlemin
eşzamanlı çalışmasını sınırlar; süresi aşan istek aynı sağlayıcı idempotency
anahtarıyla tekrarlanır. Sağlayıcı sonucu yerelde saklandıysa tekrar ağ çağrısı
yapılmaz. Ağ çağrıları transaction dışında gerçekleşir.

Tarayıcı sekmesinin kullanıcı/form bazlı session storage kaydı bekleyen işlem
kimliğini ve tekrar istek verisini saklar. Yenileme sonrasında **Kontrol et ve devam
et** aynı işlemi sürdürür. Dosya sunucuya hiç ulaşmadıysa aynı dosya yeniden
seçilmelidir. Yeni bir anahtarla tekrar üretim yapılmamalıdır. Sonuç belirsizken API
anahtarını değiştirmeyin: sağlayıcının idempotency alanı anahtar bazlıdır.

İşlem sürerken form değişmiş/silinmişse eski anlık görüntüyle üzerine yazılmaz.
Ayrılan numara korunur ve `409` döner; operatör Numaratör'de işlem UUID'sini
`external_reference` ile inceleyebilir. Sayacı geri almak, numarayı iptal etmek,
`used` durumuna geçirmek ve yeniden numaralandırmak otomatik değildir. Form silme
üretim izini silmez. Başarısız işlemlerin saklanan dosyaları tekrar deneme için
korunur; bu kayıtlar rutin dosya temizliğinde sahipsiz dosya sayılmamalıdır.

Testler gerçek Numaratör çağırmadan adapter sınırında mock kullanır. PostgreSQL'de
satır kilidi, SQLite'ta işlem yazma kilidi ve benzersiz hedef kısıtı kullanılır;
üretim ortamında gerçek sağlayıcıyla kabul testi ayrıca yapılmalıdır.
