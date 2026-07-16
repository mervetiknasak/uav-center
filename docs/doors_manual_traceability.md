# DOORS Connector - DXL Manual İzlenebilirliği

Kullanıcı tarafından sağlanan `dxl_reference_manual.pdf`, kendi giriş bölümünde
Rational DOORS 9.6.1 için DXL Reference Manual olduğunu belirtir. Connector
hedefi DOORS 9.7.0'dır; bu nedenle DXL köprüsü yalnız bu manual'da bulunan
arayüzleri kullanır. 9.7.0 ürün bağlamı ve çalıştırma seçenekleri yalnız IBM'in
resmî 9.7.0 belgeleriyle doğrulanmıştır; undocumented DXL perm kullanılmamıştır.

Sayfa numaraları PDF görüntüleyicisinin fiziksel sayfası değil, manual içinde
basılı olan sayfa numarasıdır.

| Connector alanı | Kullanılan DXL yüzeyi | Manual bölümü / sayfa |
|---|---|---|
| Dış uygulama taşıması | `DOORS.Application`, `Result`, `runFile`, `runStr`; DXL tarafında `oleGetResult`, `oleSetResult` | OLE objects / Automation client support, 769; Controlling Rational DOORS from applications that support automation, 773-775 |
| UTF-8 dosya protokolü | `Stream`, `read`, `write`, `close`, `flush`, `end`, `CP_UTF8` | Files and streams, 136-141; Codepages, 208-209 |
| Hex codec | `Buffer`, `+=`, buffer character extraction, `charOf`, `intOf(char)`, `length` | Character operations, 120-121; Text buffers, 165-171; String operations, 128-130 |
| Hata yakalama | `noError`, `lastError` | General functions / Error handling, 914-915 |
| Bağlantı bilgisi | `getDatabaseName`, `doorsname`, `username`, `hostname`, `platform` | Database properties, 215; Operating system interface, 179-183; predefined variables/general functions |
| Hiyerarşi okuma | `folder`, `item`, `for Item in Folder`, `name`, `fullName`, `description`, `type`, `uniqueID` | Hierarchy information, 272-275; Items, 279-281; Folders, 281-284 |
| Klasör oluşturma | `create(string, description, Folder&)` | Folders, 283-284 |
| Modül açma/kapama | `module`, `open`, `read`, `edit`, `save`, `close` | Modules, 293-303 |
| Formal modül oluşturma | `create(string, description, prefix, int, Module&)` | Modules / create formal module, 299-300 |
| Modül bilgisi | `version`, `baseline`, `canRead`, `canWrite`, hierarchy information perms | Modules, 296-299; Hierarchy information, 272-275 |
| Nesne bulma/listeleme | `object`, `for Object in entire(Module)`, `identifier`, `number`, `level`, `isDeleted` | Objects, 374-388 |
| Native tablo elemanı filtresi | `table(Object)`, `row(Object)`, `cell(Object)` | Tables, 822 |
| Nesne oluşturma | `create(Module)`, `create(after(Object))`, `create(last(below(Object)))` | Object management, 382-384 |
| Geri alınabilir silme | `softDelete(Object, bool)` | Object management, 385-386 |
| Öznitelik okuma | dinamik attribute reference, `unicodeString`, `canRead` | Attributes, 433-438 |
| Öznitelik tanımları | `AttrDef`, `find`, `attributeValue`, definition properties; `AttrType`, `AttrBaseType`, `stringOf` | Attribute definitions, 441-453; Attribute types, 454-462 |
| Tipli öznitelik yazma | attribute assignment for string/int/real/bool/Date; `intOf`, `realOf`, `dateOf` | Attributes, 433-434; Integer/real operations, 121-127; Dates, 149-152 |
| Link oluşturma | `Object -> string -> Object` | Links / Link creation, 396-397 |
| Giden linkleri okuma | outgoing link iterator, `module(Link)`, `target`, `targetAbsNo` | Finding links, 397-403; Link management, 410-412 |
| Link silme | `delete(Link)`, `flushDeletions` | Link management, 410; Object management / flush deletions, 385 |
| DXL çalışma limiti | `pragma runLim, 0` | Pragmas, 9; batch mode guidance, 9 |

## Bilinçli olarak kullanılmayan yüzeyler

- `runStr` manual'da doğrulanmıştır, fakat gelen verinin koda dönüşmesini
  engellemek için connector API'sinde kullanılmaz.
- `system` manual'da doğrulanmıştır, fakat işletim sistemi komutu çalıştırma
  yüzeyi açmamak için kullanılmaz.
- `eval`/`evalTop` kullanılmaz.
- `hardDelete`, `purge`, `purgeObject_` ve `purgeObjects_` kullanılmaz.
- DXL IPC perm'leri manual'da vardır; manual örnekler için kapsam dışındaki
  Rational DOORS API Manual'a yönlendirdiği için bu connector'da kullanılmaz.
- OSLC DXL Service perm'leri manual'da vardır; seçilen yerel istemci mimarisinde
  DWA/interoperation server/OAuth bağımlılığı gerekmediği için kullanılmaz.

