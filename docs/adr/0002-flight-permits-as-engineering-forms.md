# ADR-0002: Uçuş izinlerini mühendislik form motorunda tutma

- Durum: Kabul edildi
- Tarih: 2026-08-20

## Bağlam

Uçuş izinleri ayrı model, API, şablon kataloğu ve frontend ekranıyla yönetilirken
aynı ürün içinde mühendislik formları için ikinci bir dinamik form motoru oluşmuştu.
Form envanterindeki `FM.QUA.0579`, `FM.QUA.0580` ve `FM.QUA.0581` zaten uçuş izni
başvuru, koşul onayı ve onay belgesi şablonlarını temsil etmektedir.

## Karar

Uçuş izinleri `form_processes` domain'inin `flight-permits` sürecidir. Yeni izinler
`FormProcessRecord` olarak oluşturulur; şablon doğrulaması, durum geçişi, güvenli
dosya eki ve Word çıktısı genel mühendislik form akışını kullanır. Ayrı
`FlightPermit` modeli, `/api/flight-permits/` API'si ve frontend feature'ı kaldırılır.

Mevcut izin kayıtları ileri yönlü migration ile şablon koduna göre eşlenir:

- `institution_a` → `FM.QUA.0579`
- `institution_b` → `FM.QUA.0580`
- `institution_c` → `FM.QUA.0581`

Kayıt kimliği, kullanıcı audit alanları, tarihler, durum, şablona özgü veriler ve
dosya referansları korunur. Askıya alınmış veya iptal edilmiş kayıtlar genel form
yaşam döngüsünde arşivlenir; özgün durumları form verisinde tutulur.

## Sonuçlar

- Tek form kataloğu, editör, API ve veri modeli vardır.
- Uçuş izni alanları diğer dinamik formlarla aynı doğrulama ve yetki sınırındadır.
- Form ekleri tüm mühendislik kayıtları için kullanılabilir.
- Eski uçuş izni API istemcileri yeni `/api/form-processes/` sözleşmesine geçmelidir.
