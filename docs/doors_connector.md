# IBM DOORS 9.7.0 Python Connector

Bu connector, aynı Windows oturumundaki IBM Engineering Requirements Management
DOORS istemcisiyle Python arasında yerel ve senkron haberleşme kurar. Üretim
taşıması, DXL Reference Manual'da dış uygulamaların DOORS'u kontrol etmesi için
tanımlanan `DOORS.Application` OLE Automation nesnesini kullanır.

Connector serbest DXL çalıştırmaz. Python yalnız sabit bir işlem adı ve veri
alanları gönderir. DXL köprüsü bu alanları kod olarak değerlendirmez.

## Neden OLE Automation?

Değerlendirilen doğrulanmış seçenekler:

| Yöntem | Doğrulanmış özellik | Bu uygulamadaki karar |
|---|---|---|
| OLE Automation | Manual, `DOORS.Application`, `runFile`, `runStr` ve çift yönlü `Result` özelliğini dış uygulamalar için tanımlar. | Yerel DOORS 9.7.0 istemcisi için ana taşıma. DWA veya ek sunucu gerektirmez. |
| OSLC DXL Service | IBM 9.7.0 belgesi HTTP/HTTPS, DWA, interoperation server, service discovery ve OAuth akışını tanımlar. | Uzak/sunucu kurulumu için geçerli, fakat mevcut yerel connector için gereksiz altyapı bağımlılığı oluşturur. |
| Batch (`-b`) | IBM 9.7.x belgesi GUI olmadan bir DXL dosyası çalıştırıp istemciyi kapattığını doğrular. | Tek seferlik işler için uygun; düşük gecikmeli çift yönlü connector oturumu için seçilmedi. |
| DXL TCP/IP IPC | Manual Windows ve UNIX üzerinde TCP/IP IPC perm'lerini tanımlar, fakat örnekler için ayrı DOORS API Manual'a yönlendirir. | Kullanıcının yalnız ekli manual sınırı nedeniyle özel bir ağ protokolü uygulanmadı. |

IBM kaynakları:

- [DOORS 9.7.0 - OSLC DXL services](https://www.ibm.com/docs/en/engineering-lifecycle-management-suite/doors/9.7.0?topic=services-oslc-dxl-doors)
- [DOORS 9.7.0 - Starting DOORS from the command line](https://www.ibm.com/docs/en/engineering-lifecycle-management-suite/doors/9.7.0?topic=client-starting-doors-from-command-line)
- [DOORS client command-line switches](https://www.ibm.com/docs/en/engineering-lifecycle-management-suite/doors/9.7.1?topic=client-command-line-switches-doors)
- [DOORS 9.7.0 - Setting up DXL security](https://www.ibm.com/docs/en/engineering-lifecycle-management-suite/doors/9.7.0?topic=dxl-setting-up-security)
- [DOORS and DOORS Web Access 9.7 release](https://www.ibm.com/support/pages/doors-and-doors-web-access-97)

IBM'in 9.7 ilk sürüm sayfası, `PH10756` (DXL stream yazımında access
violation) düzeltmesini 9.7 ile çözülen APAR'lar arasında listeler. Connector'ın
dosya protokolü stream kullandığı için bu sürüm doğrulaması özellikle dikkate
alınmıştır.

DXL kodundaki bütün perm ve veri tipleri, kullanıcı tarafından sağlanan
`dxl_reference_manual.pdf` içinden alınmıştır. Ayrıntılı eşleştirme
[`doors_manual_traceability.md`](doors_manual_traceability.md) dosyasındadır.

## Ön koşullar

- IBM DOORS 9.7.0 Windows istemcisi kurulu ve `DOORS.Application` Automation
  nesnesi kayıtlı olmalıdır.
- Python 3.11 ve Windows koşullu `pywin32` bağımlılığı kurulmalıdır.
- Connector'ı çalıştıran Windows kullanıcısı DOORS'a giriş yapmış olmalıdır.
  Connector parola saklamaz, komut satırına parola yazmaz ve `SendKeys`
  kullanmaz.
- Kurumun DXL Security ayarları, bridge dosyasının `runFile` ile çalıştırılmasına
  izin vermelidir.
- Python süreci ile DOORS istemcisi aynı makinede çalışmalıdır. İstek/yanıt
  dosyaları her iki süreç tarafından erişilebilir olmalıdır.

Kurulum:

```powershell
cd backend
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Ayarlar

Varsayılan bridge proje içindeki
`backend/api/services/dxl/doors_connector_bridge.dxl` dosyasıdır.

```env
DOORS_DXL_BRIDGE=C:\uav-center\backend\api\services\dxl\doors_connector_bridge.dxl
DOORS_TEMP_DIR=C:\Users\service-user\AppData\Local\Temp\doors-connector
DOORS_LOCK_TIMEOUT=60
```

`DOORS_DXL_BRIDGE` tam yol olmalıdır. Manual'ın `runFile` açıklamasına göre DXL
dosyası UTF-8 olmalıdır. Birden çok Python worker aynı `DOORS.Application.Result`
özelliğini paylaştığı için connector hem thread kilidi hem de
`DOORS_TEMP_DIR/automation.lock` süreç kilidi kullanır. Tüm worker'lar aynı
`DOORS_TEMP_DIR` değerini kullanmalıdır.

## Hızlı bağlantı kontrolü

DOORS istemcisini açıp giriş yaptıktan sonra:

```powershell
cd backend
py manage.py shell -c "from api.services.doors_connector import DoorsConnector; print(DoorsConnector().check_connection())"
```

Başarılı cevap; protokol sürümü, veritabanı adı, DOORS kullanıcısı, işletim
sistemi kullanıcısı, host ve platform bilgisini içerir.

## Python API

```python
from api.services.doors_connector import DoorsConnector, DoorsDate

doors = DoorsConnector()

info = doors.check_connection()
items = doors.list_items("/UAV", recursive=True)
module = doors.get_module("/UAV/System Requirements")
attributes = doors.list_attributes(
    "/UAV/System Requirements",
    scope="object",
)

page = doors.list_objects(
    "/UAV/System Requirements",
    attributes=["Object Heading", "Object Text", "Priority"],
    offset=0,
    limit=100,
)

created = doors.create_object(
    "/UAV/System Requirements",
    {
        "Object Heading": "Flight control",
        "Object Text": "The UAV shall maintain commanded attitude.",
        "Priority": "High",
        "Approved": True,
        "Review Date": DoorsDate(1782864000),
    },
)

doors.update_object(
    "/UAV/System Requirements",
    created.absolute_number,
    {"Object Text": "The UAV shall maintain commanded attitude within limits."},
)
```

Desteklenen sabit işlemler:

- bağlantı kontrolü;
- klasör/proje/modül hiyerarşisini yinelemeli veya tek seviyeli listeleme;
- modül bilgisi, modül/nesne öznitelik tanımları ve modül öznitelik değerleri;
- sayfalı nesne listeleme ve mutlak numarayla nesne okuma;
- klasör ve formal modül oluşturma;
- nesne oluşturma, güncelleme ve geri alınabilir soft delete;
- modül özniteliklerini güncelleme;
- giden linkleri listeleme, link oluşturma ve tekil eşleşen linki silme.

`list_objects` varsayılan olarak DOORS native tablo başlıklarını, satır
başlıklarını, hücreleri ve soft-delete nesneleri dışarıda bırakır. Okuma yetkisi
olmayan bir öznitelik değeri Python'da `None` olarak döner; boş ama okunabilir
değer `""` olarak döner.

## Değer tipleri

Python değerleri DXL'e tip etiketiyle taşınır ve manual'daki öznitelik tipi
bilgisiyle doğrulanır:

- `str`: DXL `attributeValue` doğrulamasından geçen String, Text, Enumeration
  veya dönüştürülebilir bir skaler değer;
- `int`: yalnız Integer tabanlı öznitelik;
- `float`: yalnız Real tabanlı öznitelik;
- `bool`: yalnız iki elemanlı Enumeration; manual'daki boolean atamasına göre
  `False` ilk, `True` ikinci elemana eşlenir;
- `DoorsDate(seconds)`: `dateOf(int)` ile Date özniteliğine yazılan, 1 Ocak 1970
  00:00:00 GMT'den itibaren saniye;
- `None`: boş string olarak gönderilir ve yalnız öznitelik tipi bu değeri kabul
  ederse yazılır.

## Yazma güvenliği ve hata davranışı

- Connector, kullanıcının zaten açık tuttuğu bir modüle yazmaz. Bu, kullanıcının
  kaydedilmemiş değişikliklerine karışmayı önler.
- Yazılacak bütün öznitelikler oluşturma/güncelleme öncesinde varlık, kapsam,
  kullanıcı erişimi, yazma yetkisi ve değer geçerliliği bakımından doğrulanır.
- Connector'ın açtığı modül üzerinde hata oluşursa modül kaydetmeden kapatılır.
  Başarılı durumda `save(Module)` çağrılır ve modül kapatılır.
- Nesne silme `softDelete` kullanır; purge/hard delete API yüzeyi yoktur.
- Link silme, kaynak/link modülü/hedef/mutlak numara bileşimiyle tam bir eşleşme
  arar. Sıfır veya birden fazla eşleşmede veri değiştirmez.
- DXL runtime mesajları modal kutuya çevrilmez; `noError`/`lastError` ile yakalanıp
  tipli `DoorsConnectorError` olarak döndürülür.

## Protokol

İstek ve yanıtlar yalnız connector'ın oluşturduğu benzersiz geçici dizinde
tutulur. Her alan UTF-8 byte dizisinin hexadecimal ASCII gösterimidir. Böylece
satır sonu, yüzde, tırnak ve DXL sözdizimi karakterleri veri olarak kalır.

Köprü şu güvenlik sınırlarını uygular:

- en fazla 1024 istek alanı;
- nesne sayfasında en fazla 1000 kayıt;
- çağrı başına en fazla 200 öznitelik;
- yalnız dispatch tablosunda bulunan işlem adları;
- `eval`, `evalTop`, `system` ve gelen içerikle `runStr` yoktur.

## DOORS üzerinde kabul testi

Bu depo DOORS çalıştırmayan ortamlarda Python protokol ve mapping testlerini
çalıştırabilir. Gerçek DXL yorumlayıcı kabul testi, lisanslı DOORS 9.7.0 Windows
istemcisinde yapılmalıdır:

1. Üretim veritabanından bağımsız bir test projesi ve formal modül oluşturun.
2. Bağlantı kontrolünü ve salt-okunur listeleme işlemlerini çalıştırın.
3. String, Integer, Real, iki elemanlı Enumeration ve Date öznitelikleri üzerinde
   birer yazma testi yapın.
4. Aynı modülü DOORS arayüzünde açık tutarken yazma çağrısının
   `MODULE_EDIT_FAILED` ile reddedildiğini doğrulayın.
5. Bir test nesnesini soft-delete edin ve DOORS arayüzünden geri alınabildiğini
   doğrulayın.
6. Test link modülüyle link oluşturma, listeleme ve silme akışını doğrulayın.
7. Kurumun DXL Security kısıtlarını etkinleştirip yalnız onaylı bridge yolunun
   çalıştığını doğrulayın.

DOORS üzerinde bu kabul testi yapılmadan connector için “üretimde doğrulandı”
iddiasında bulunulmamalıdır.
