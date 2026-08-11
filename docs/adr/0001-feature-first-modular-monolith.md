# ADR-0001: Feature-first modular monolith

- Durum: Kabul edildi
- Tarih: 2026-08-11

## Bağlam

Tek Django `api` uygulamasında çok sayıda bağımsız domain aynı model, serializer ve
view dosyalarında büyümüştür. Yeni Django app'lerine fiziksel model taşıma tablo,
content-type ve migration app-label değişikliği oluşturacaktır.

## Karar

`api` app-label'ı korunacak; kod accounts, documents, jobs, organization,
technical documents, flight permits, AI ve meeting minutes feature paketlerine
ayrılacaktır. Root model/serializer/view dosyaları açık re-export façade olacaktır.

Frontend, uygulama context'i ile feature-owned lazy route controller'larına
ayrılacak; `App.vue` iş özelliği orkestrasyonu yapmayacaktır.

## Sonuçlar

- Mevcut şema ve migration geçmişi korunur.
- Feature sahipliği ve test yüzeyi belirginleşir.
- Façade dosyaları geçiş maliyeti getirir fakat yeni kod barındırmaz.
- Mikroservis operasyon maliyeti oluşmaz; gerektiğinde kararlı port üzerinden
  servis çıkarımı yapılabilir.

