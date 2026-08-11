# ADR-0004: Belge sahipliği, denetim ve retention

- Durum: Kabul edildi
- Tarih: 2026-08-11

## Bağlam

Belge kayıtlarında owner bulunmadığı için herhangi bir aktif kullanıcı başka bir
kullanıcının belgesini listeleyebiliyor, içeriğini/RAG sonucunu okuyabiliyor ve
silebiliyordu. Buna karşılık job ve analiz kontrolleri kullanıcıya özeldi. Bu
tutarsızlık kurum içi belge gizliliği ve nesne düzeyi yetkilendirme riski oluşturdu.

## Karar

`Document.owner` nullable bir kullanıcı ilişkisi olarak eklenir. Migration yalnız
bir belgenin bütün mevcut job'ları aynı kullanıcıya aitse owner'ı geriye dönük
çıkarır; belirsiz veya job'sız kayıtları tahmin etmez. Normal kullanıcı yalnız
kendi belgelerine ve analizlerine erişir. Staff bütün belgeleri, owner bilgisini ve
belge analiz geçmişini denetleyebilir; owner'ı belirlenemeyen legacy kayıtlar yalnız
staff'a görünür. Job ve özel analiz kontrolleri sahibine özel kalır.

Kullanıcı silinmesi kurumsal belgeyi silmez: owner `SET_NULL` olur ve kayıt staff
denetim/retention alanında kalır. Dosya silme, veritabanı commit'inden sonra
çalıştırılır; ingestion rollback'i ise orphan dosyayı compensating cleanup ile
kaldırır.

## Sonuçlar

- URL kimliğini bilen başka kullanıcı kaynak varlığını öğrenmez; filtreli queryset
  `404` üretir.
- Staff rolü hassas belge içeriğine erişebilen güvenilir denetim rolüdür ve bu yetki
  deployment rol politikasında açıkça yönetilmelidir.
- Owner'ı belirsiz eski kayıtlar otomatik olarak yanlış kullanıcıya atanmaz.
- İleride proje/tenant paylaşımı gerekirse owner filtresi sessizce gevşetilmez;
  açık üyelik modeli, veri migration'ı ve negatif yetki testleri eklenir.
