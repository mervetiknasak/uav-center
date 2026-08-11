"""IBM Engineering Requirements Management DOORS 9.7 connector.

The production transport uses the ``DOORS.Application`` OLE Automation object
documented by IBM's DXL Reference Manual.  Only a fixed command vocabulary is
accepted by the bundled DXL bridge; callers cannot submit arbitrary DXL.
"""

from __future__ import annotations

import sys
import tempfile
import threading
import time
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

try:
    from django.conf import settings
except ImportError:  # pragma: no cover - permits reuse outside Django
    settings = None


PROTOCOL_VERSION = "DXLC/1"
AUTOMATION_PROG_ID = "DOORS.Application"
MAX_ARGUMENTS = 1024
MAX_PAGE_SIZE = 1000
_AUTOMATION_THREAD_LOCK = threading.RLock()


class DoorsConnectorError(RuntimeError):
    """Normalized connector, transport, protocol, or DXL operation error."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "CONNECTOR_ERROR",
        operation: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.operation = operation


@dataclass(frozen=True)
class DoorsConfig:
    """Local DOORS Automation configuration.

    The bridge must be on the same Windows host as the DOORS client because
    ``runFile`` receives a local absolute path.
    """

    bridge_path: Path = Path(__file__).with_name("dxl") / "doors_connector_bridge.dxl"
    temp_dir: Path | None = None
    lock_timeout: float = 60.0

    @classmethod
    def from_settings(cls) -> DoorsConfig:
        def value(name: str, default: Any) -> Any:
            if settings is None or not getattr(settings, "configured", False):
                return default
            return getattr(settings, name, default)

        default_bridge = cls().bridge_path
        bridge = Path(value("DOORS_DXL_BRIDGE", default_bridge)).expanduser()
        temp_value = value("DOORS_TEMP_DIR", None)
        return cls(
            bridge_path=bridge.resolve(),
            temp_dir=Path(temp_value).expanduser().resolve() if temp_value else None,
            lock_timeout=float(value("DOORS_LOCK_TIMEOUT", 60.0)),
        )

    def validate(self, *, require_windows: bool = True) -> None:
        if require_windows and sys.platform != "win32":
            raise DoorsConnectorError(
                "DOORS OLE Automation taşıması yalnızca Windows üzerinde çalışır.",
                code="UNSUPPORTED_PLATFORM",
            )
        if self.lock_timeout <= 0:
            raise DoorsConnectorError(
                "DOORS kilit timeout değeri sıfırdan büyük olmalıdır.",
                code="INVALID_CONFIG",
            )
        if not self.bridge_path.is_absolute():
            raise DoorsConnectorError(
                "DOORS DXL bridge yolu mutlak olmalıdır.",
                code="INVALID_CONFIG",
            )
        if not self.bridge_path.is_file():
            raise DoorsConnectorError(
                f"DOORS DXL bridge bulunamadı: {self.bridge_path}",
                code="BRIDGE_NOT_FOUND",
            )
        if self.temp_dir is not None and not self.temp_dir.is_dir():
            raise DoorsConnectorError(
                f"DOORS geçici dizini bulunamadı: {self.temp_dir}",
                code="INVALID_CONFIG",
            )


@dataclass(frozen=True)
class DoorsInfo:
    protocol_version: str
    database_name: str
    doors_user: str
    os_user: str
    hostname: str
    platform: str


@dataclass(frozen=True)
class HierarchyItem:
    name: str
    full_name: str
    item_type: str
    description: str
    unique_id: str


@dataclass(frozen=True)
class ModuleInfo:
    name: str
    full_name: str
    module_type: str
    description: str
    unique_id: str
    version: str
    is_baseline: bool
    can_read: bool
    can_write: bool


@dataclass(frozen=True)
class AttributeDefinition:
    name: str
    type_name: str
    base_type: str
    object_scope: bool
    module_scope: bool
    multi_value: bool
    system: bool
    user_access: bool


@dataclass(frozen=True)
class DoorsObject:
    absolute_number: int
    identifier: str
    number: str
    level: int
    attributes: Mapping[str, str | None]


@dataclass(frozen=True)
class ObjectPage:
    items: tuple[DoorsObject, ...]
    offset: int
    next_offset: int
    has_more: bool


@dataclass(frozen=True)
class DoorsLink:
    source_absolute_number: int
    link_module: str
    target_module: str
    target_absolute_number: int


@dataclass(frozen=True)
class DoorsDate:
    """A DOORS Date attribute value expressed as seconds since 1970-01-01 GMT."""

    seconds_since_epoch: int

    def __post_init__(self) -> None:
        if self.seconds_since_epoch < 0:
            raise ValueError("DOORS Date saniye değeri negatif olamaz.")


class DoorsTransport(Protocol):
    def call(self, operation: str, arguments: Sequence[str]) -> list[str]: ...


class _AutomationObject(Protocol):
    Result: str

    def runFile(self, dxl_file_name: str) -> Any: ...


def _hex_encode(value: str) -> str:
    return value.encode("utf-8").hex().upper()


def _hex_decode(value: str) -> str:
    try:
        return bytes.fromhex(value).decode("utf-8")
    except (ValueError, UnicodeDecodeError) as exc:
        raise DoorsConnectorError(
            "DXL bridge geçersiz UTF-8/hex alan döndürdü.",
            code="INVALID_RESPONSE",
        ) from exc


def _write_request(
    path: Path,
    response_path: Path,
    operation: str,
    arguments: Sequence[str],
) -> None:
    if not operation or any(ch not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ_" for ch in operation):
        raise DoorsConnectorError("Geçersiz DOORS işlem adı.", code="INVALID_REQUEST")
    if len(arguments) > MAX_ARGUMENTS:
        raise DoorsConnectorError(
            f"Bir çağrıda en fazla {MAX_ARGUMENTS} argüman gönderilebilir.",
            code="INVALID_REQUEST",
            operation=operation,
        )
    lines = [
        _hex_encode(str(response_path)),
        PROTOCOL_VERSION,
        _hex_encode(operation),
        str(len(arguments)),
        *(_hex_encode(str(argument)) for argument in arguments),
    ]
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


def _read_response(path: Path, operation: str) -> list[str]:
    try:
        response_text = path.read_text(encoding="utf-8-sig")
        response_text.encode("ascii")
        lines = response_text.splitlines()
    except FileNotFoundError as exc:
        raise DoorsConnectorError(
            "DXL bridge yanıt dosyası oluşturmadı.",
            code="NO_RESPONSE",
            operation=operation,
        ) from exc
    except (UnicodeDecodeError, UnicodeEncodeError) as exc:
        raise DoorsConnectorError(
            "DXL bridge yanıtı ASCII protokolünde değil.",
            code="INVALID_RESPONSE",
            operation=operation,
        ) from exc

    if len(lines) < 3 or lines[0] != PROTOCOL_VERSION or lines[1] not in {"OK", "ERR"}:
        raise DoorsConnectorError(
            "DXL bridge yanıt başlığı geçersiz.",
            code="INVALID_RESPONSE",
            operation=operation,
        )
    try:
        field_count = int(lines[2])
    except ValueError as exc:
        raise DoorsConnectorError(
            "DXL bridge alan sayısı geçersiz.",
            code="INVALID_RESPONSE",
            operation=operation,
        ) from exc
    if field_count < 0 or len(lines) != field_count + 3:
        raise DoorsConnectorError(
            "DXL bridge yanıt uzunluğu alan sayısıyla uyuşmuyor.",
            code="INVALID_RESPONSE",
            operation=operation,
        )
    fields = [_hex_decode(value) for value in lines[3:]]
    if lines[1] == "ERR":
        code = fields[0] if fields else "DXL_ERROR"
        message = fields[1] if len(fields) > 1 else "DOORS DXL işlemi başarısız."
        raise DoorsConnectorError(message, code=code, operation=operation)
    return fields


@contextmanager
def _interprocess_lock(path: Path, timeout: float) -> Iterator[None]:
    """Serialize access to the process-global DOORS Automation Result property."""

    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("a+b")
    locked = False
    try:
        if sys.platform == "win32":
            import msvcrt

            if path.stat().st_size == 0:
                handle.write(b"0")
                handle.flush()
            deadline = time.monotonic() + timeout
            while True:
                try:
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                    locked = True
                    break
                except OSError as exc:
                    if time.monotonic() >= deadline:
                        raise DoorsConnectorError(
                            "DOORS Automation kilidi zaman aşımına uğradı.",
                            code="LOCK_TIMEOUT",
                        ) from exc
                    time.sleep(0.05)
        yield
    finally:
        if locked:
            import msvcrt

            handle.seek(0)
            msvcrt.locking(  # type: ignore[attr-defined]
                handle.fileno(),
                msvcrt.LK_UNLCK,  # type: ignore[attr-defined]
                1,
            )
        handle.close()


class OleAutomationTransport:
    """Synchronous local transport over IBM's ``DOORS.Application`` COM API."""

    def __init__(
        self,
        config: DoorsConfig | None = None,
        *,
        automation: _AutomationObject | None = None,
    ) -> None:
        self.config = config or DoorsConfig.from_settings()
        self._automation = automation
        self.config.validate(require_windows=automation is None)

    def _dispatch(self) -> tuple[_AutomationObject, Any | None]:
        if self._automation is not None:
            return self._automation, None
        try:
            import pythoncom
            from win32com.client import Dispatch
        except ImportError as exc:  # pragma: no cover - Windows deployment only
            raise DoorsConnectorError(
                "DOORS connector için pywin32 kurulu olmalıdır.",
                code="MISSING_DEPENDENCY",
            ) from exc
        pythoncom.CoInitialize()
        try:
            return Dispatch(AUTOMATION_PROG_ID), pythoncom
        except Exception:
            pythoncom.CoUninitialize()
            raise

    def call(self, operation: str, arguments: Sequence[str]) -> list[str]:
        temp_root = str(self.config.temp_dir) if self.config.temp_dir else None
        lock_root = self.config.temp_dir or Path(tempfile.gettempdir()) / "doors-python-connector"
        lock_path = lock_root / "automation.lock"

        with _AUTOMATION_THREAD_LOCK, _interprocess_lock(lock_path, self.config.lock_timeout):
            with tempfile.TemporaryDirectory(prefix="dxlc-", dir=temp_root) as directory:
                request_path = Path(directory) / "request.dxlc"
                response_path = Path(directory) / "response.dxlc"
                _write_request(request_path, response_path, operation, arguments)
                automation: _AutomationObject | None = None
                pythoncom: Any | None = None
                try:
                    automation, pythoncom = self._dispatch()
                    automation.Result = str(request_path)
                    automation.runFile(str(self.config.bridge_path))
                    completion = str(automation.Result)
                except DoorsConnectorError:
                    raise
                except Exception as exc:
                    raise DoorsConnectorError(
                        f"DOORS OLE Automation çağrısı başarısız: {exc}",
                        code="AUTOMATION_ERROR",
                        operation=operation,
                    ) from exc
                finally:
                    if pythoncom is not None:
                        automation = None
                        pythoncom.CoUninitialize()
                if completion != f"{PROTOCOL_VERSION}:OK":
                    raise DoorsConnectorError(
                        "DXL bridge tamamlanma belirtecini döndürmedi. DOORS DXL çıktısını inceleyin.",
                        code="BRIDGE_NOT_COMPLETED",
                        operation=operation,
                    )
                return _read_response(response_path, operation)


def _bool(value: str) -> bool:
    if value == "1":
        return True
    if value == "0":
        return False
    raise DoorsConnectorError("DXL bridge boolean alanı geçersiz.", code="INVALID_RESPONSE")


def _int(value: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise DoorsConnectorError(
            "DXL bridge integer alanı geçersiz.", code="INVALID_RESPONSE"
        ) from exc


def _expect(fields: Sequence[str], count: int, operation: str) -> None:
    if len(fields) != count:
        raise DoorsConnectorError(
            f"{operation} yanıtı {count} alan yerine {len(fields)} alan içeriyor.",
            code="INVALID_RESPONSE",
            operation=operation,
        )


def _attribute_arguments(values: Mapping[str, Any]) -> list[str]:
    if not values:
        raise DoorsConnectorError("En az bir öznitelik değeri gereklidir.", code="INVALID_REQUEST")
    result = [str(len(values))]
    for name, value in values.items():
        if not isinstance(name, str) or not name:
            raise DoorsConnectorError("Öznitelik adı boş olamaz.", code="INVALID_REQUEST")
        if isinstance(value, bool):
            value_kind = "BOOLEAN"
            normalized = "1" if value else "0"
        elif isinstance(value, DoorsDate):
            value_kind = "DATE"
            normalized = str(value.seconds_since_epoch)
        elif isinstance(value, int):
            value_kind = "INTEGER"
            normalized = str(value)
        elif isinstance(value, float):
            value_kind = "REAL"
            normalized = str(value)
        elif value is None:
            value_kind = "STRING"
            normalized = ""
        else:
            value_kind = "STRING"
            normalized = str(value)
        result.extend((name, value_kind, normalized))
    return result


def _normalized_attribute_values(values: Mapping[str, Any]) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for name, value in values.items():
        if isinstance(value, bool):
            normalized[name] = "1" if value else "0"
        elif isinstance(value, DoorsDate):
            normalized[name] = str(value.seconds_since_epoch)
        elif value is None:
            normalized[name] = ""
        else:
            normalized[name] = str(value)
    return normalized


class DoorsConnector:
    """Typed, fixed-operation façade for DOORS hierarchy and requirement data."""

    def __init__(
        self,
        config: DoorsConfig | None = None,
        *,
        transport: DoorsTransport | None = None,
    ) -> None:
        self.config = config or DoorsConfig.from_settings()
        self.transport = transport or OleAutomationTransport(self.config)

    def _call(self, operation: str, arguments: Sequence[Any] = ()) -> list[str]:
        return self.transport.call(operation, [str(value) for value in arguments])

    def check_connection(self) -> DoorsInfo:
        operation = "PING"
        fields = self._call(operation)
        _expect(fields, 6, operation)
        return DoorsInfo(*fields)

    def list_items(self, folder_path: str = "/", *, recursive: bool = True) -> list[HierarchyItem]:
        operation = "LIST_ITEMS"
        fields = self._call(operation, (folder_path, "1" if recursive else "0"))
        if not fields:
            raise DoorsConnectorError("LIST_ITEMS boş yanıt döndürdü.", code="INVALID_RESPONSE")
        count = _int(fields[0])
        _expect(fields, 1 + count * 5, operation)
        return [HierarchyItem(*fields[1 + index * 5 : 6 + index * 5]) for index in range(count)]

    def get_module(self, module_path: str) -> ModuleInfo:
        operation = "GET_MODULE"
        fields = self._call(operation, (module_path,))
        _expect(fields, 9, operation)
        return ModuleInfo(
            name=fields[0],
            full_name=fields[1],
            module_type=fields[2],
            description=fields[3],
            unique_id=fields[4],
            version=fields[5],
            is_baseline=_bool(fields[6]),
            can_read=_bool(fields[7]),
            can_write=_bool(fields[8]),
        )

    def list_attributes(
        self,
        module_path: str,
        *,
        scope: str = "object",
    ) -> list[AttributeDefinition]:
        if scope not in {"object", "module", "all"}:
            raise DoorsConnectorError(
                "scope object, module veya all olmalıdır.", code="INVALID_REQUEST"
            )
        operation = "LIST_ATTRIBUTES"
        fields = self._call(operation, (module_path, scope))
        if not fields:
            raise DoorsConnectorError(
                "LIST_ATTRIBUTES boş yanıt döndürdü.", code="INVALID_RESPONSE"
            )
        count = _int(fields[0])
        width = 8
        _expect(fields, 1 + count * width, operation)
        result = []
        for index in range(count):
            row = fields[1 + index * width : 1 + (index + 1) * width]
            result.append(
                AttributeDefinition(
                    name=row[0],
                    type_name=row[1],
                    base_type=row[2],
                    object_scope=_bool(row[3]),
                    module_scope=_bool(row[4]),
                    multi_value=_bool(row[5]),
                    system=_bool(row[6]),
                    user_access=_bool(row[7]),
                )
            )
        return result

    def list_objects(
        self,
        module_path: str,
        *,
        attributes: Sequence[str] = ("Object Heading", "Object Text"),
        offset: int = 0,
        limit: int = 100,
    ) -> ObjectPage:
        if offset < 0 or not 1 <= limit <= MAX_PAGE_SIZE:
            raise DoorsConnectorError(
                f"offset >= 0 ve limit 1..{MAX_PAGE_SIZE} aralığında olmalıdır.",
                code="INVALID_REQUEST",
            )
        if len(attributes) > 200 or any(not name for name in attributes):
            raise DoorsConnectorError(
                "Öznitelik listesi geçersiz veya çok büyük.", code="INVALID_REQUEST"
            )
        operation = "LIST_OBJECTS"
        args = [module_path, str(offset), str(limit), str(len(attributes)), *attributes]
        fields = self._call(operation, args)
        if len(fields) < 3:
            raise DoorsConnectorError("LIST_OBJECTS yanıtı eksik.", code="INVALID_RESPONSE")
        count, next_offset, has_more = _int(fields[0]), _int(fields[1]), _bool(fields[2])
        row_width = 4 + len(attributes) * 2
        _expect(fields, 3 + count * row_width, operation)
        objects: list[DoorsObject] = []
        cursor = 3
        for _ in range(count):
            absolute_number = _int(fields[cursor])
            identifier, number, object_level = (
                fields[cursor + 1],
                fields[cursor + 2],
                _int(fields[cursor + 3]),
            )
            cursor += 4
            values: dict[str, str | None] = {}
            for attribute_name in attributes:
                readable, value = _bool(fields[cursor]), fields[cursor + 1]
                values[attribute_name] = value if readable else None
                cursor += 2
            objects.append(DoorsObject(absolute_number, identifier, number, object_level, values))
        return ObjectPage(tuple(objects), offset, next_offset, has_more)

    def get_object(
        self,
        module_path: str,
        absolute_number: int,
        *,
        attributes: Sequence[str] = ("Object Heading", "Object Text"),
    ) -> DoorsObject:
        page = self._object_operation("GET_OBJECT", module_path, absolute_number, attributes)
        return page

    def _object_operation(
        self,
        operation: str,
        module_path: str,
        absolute_number: int,
        attributes: Sequence[str],
    ) -> DoorsObject:
        if absolute_number < 1 or len(attributes) > 200 or any(not name for name in attributes):
            raise DoorsConnectorError(
                "Nesne numarası veya öznitelik listesi geçersiz.", code="INVALID_REQUEST"
            )
        fields = self._call(
            operation,
            (module_path, absolute_number, len(attributes), *attributes),
        )
        expected = 4 + len(attributes) * 2
        _expect(fields, expected, operation)
        cursor = 4
        values: dict[str, str | None] = {}
        for attribute_name in attributes:
            readable, value = _bool(fields[cursor]), fields[cursor + 1]
            values[attribute_name] = value if readable else None
            cursor += 2
        return DoorsObject(_int(fields[0]), fields[1], fields[2], _int(fields[3]), values)

    def get_module_attributes(
        self, module_path: str, attributes: Sequence[str]
    ) -> dict[str, str | None]:
        if not attributes or len(attributes) > 200 or any(not name for name in attributes):
            raise DoorsConnectorError("Öznitelik listesi geçersiz.", code="INVALID_REQUEST")
        operation = "GET_MODULE_ATTRIBUTES"
        fields = self._call(operation, (module_path, len(attributes), *attributes))
        _expect(fields, len(attributes) * 2, operation)
        return {
            name: fields[index * 2 + 1] if _bool(fields[index * 2]) else None
            for index, name in enumerate(attributes)
        }

    def create_folder(self, path: str, *, description: str = "") -> HierarchyItem:
        operation = "CREATE_FOLDER"
        fields = self._call(operation, (path, description))
        _expect(fields, 5, operation)
        return HierarchyItem(*fields)

    def create_formal_module(
        self,
        path: str,
        *,
        description: str = "",
        prefix: str = "",
        first_absolute_number: int = 1,
    ) -> ModuleInfo:
        if first_absolute_number < 1:
            raise DoorsConnectorError(
                "İlk mutlak numara en az 1 olmalıdır.", code="INVALID_REQUEST"
            )
        operation = "CREATE_FORMAL_MODULE"
        fields = self._call(operation, (path, description, prefix, first_absolute_number))
        _expect(fields, 9, operation)
        return ModuleInfo(
            fields[0],
            fields[1],
            fields[2],
            fields[3],
            fields[4],
            fields[5],
            _bool(fields[6]),
            _bool(fields[7]),
            _bool(fields[8]),
        )

    def create_object(
        self,
        module_path: str,
        attributes: Mapping[str, Any],
        *,
        position: str = "append",
        anchor_absolute_number: int | None = None,
    ) -> DoorsObject:
        if position not in {"append", "after", "below"}:
            raise DoorsConnectorError(
                "position append, after veya below olmalıdır.", code="INVALID_REQUEST"
            )
        if position != "append" and (anchor_absolute_number is None or anchor_absolute_number < 1):
            raise DoorsConnectorError(
                "after/below için geçerli anchor gereklidir.", code="INVALID_REQUEST"
            )
        args = [
            module_path,
            position,
            str(anchor_absolute_number or 0),
            *_attribute_arguments(attributes),
        ]
        fields = self._call("CREATE_OBJECT", args)
        _expect(fields, 4, "CREATE_OBJECT")
        return DoorsObject(
            _int(fields[0]),
            fields[1],
            fields[2],
            _int(fields[3]),
            _normalized_attribute_values(attributes),
        )

    def update_object(
        self, module_path: str, absolute_number: int, attributes: Mapping[str, Any]
    ) -> DoorsObject:
        if absolute_number < 1:
            raise DoorsConnectorError(
                "Mutlak nesne numarası en az 1 olmalıdır.", code="INVALID_REQUEST"
            )
        args = [module_path, str(absolute_number), *_attribute_arguments(attributes)]
        fields = self._call("UPDATE_OBJECT", args)
        _expect(fields, 4, "UPDATE_OBJECT")
        normalized = _normalized_attribute_values(attributes)
        return DoorsObject(_int(fields[0]), fields[1], fields[2], _int(fields[3]), normalized)

    def update_module_attributes(self, module_path: str, attributes: Mapping[str, Any]) -> None:
        fields = self._call(
            "UPDATE_MODULE_ATTRIBUTES", (module_path, *_attribute_arguments(attributes))
        )
        _expect(fields, 0, "UPDATE_MODULE_ATTRIBUTES")

    def soft_delete_object(
        self,
        module_path: str,
        absolute_number: int,
        *,
        check_links: bool = True,
    ) -> None:
        if absolute_number < 1:
            raise DoorsConnectorError(
                "Mutlak nesne numarası en az 1 olmalıdır.", code="INVALID_REQUEST"
            )
        fields = self._call(
            "SOFT_DELETE_OBJECT",
            (module_path, absolute_number, "1" if check_links else "0"),
        )
        _expect(fields, 0, "SOFT_DELETE_OBJECT")

    def list_outgoing_links(
        self,
        module_path: str,
        *,
        source_absolute_number: int | None = None,
    ) -> list[DoorsLink]:
        if source_absolute_number is not None and source_absolute_number < 1:
            raise DoorsConnectorError(
                "Kaynak nesne numarası en az 1 olmalıdır.", code="INVALID_REQUEST"
            )
        operation = "LIST_OUTGOING_LINKS"
        fields = self._call(operation, (module_path, source_absolute_number or 0))
        if not fields:
            raise DoorsConnectorError(
                "LIST_OUTGOING_LINKS boş yanıt döndürdü.", code="INVALID_RESPONSE"
            )
        count = _int(fields[0])
        _expect(fields, 1 + count * 4, operation)
        return [
            DoorsLink(
                source_absolute_number=_int(fields[1 + index * 4]),
                link_module=fields[2 + index * 4],
                target_module=fields[3 + index * 4],
                target_absolute_number=_int(fields[4 + index * 4]),
            )
            for index in range(count)
        ]

    def create_link(
        self,
        source_module: str,
        source_absolute_number: int,
        link_module: str,
        target_module: str,
        target_absolute_number: int,
    ) -> DoorsLink:
        if source_absolute_number < 1 or target_absolute_number < 1 or not link_module:
            raise DoorsConnectorError("Link parametreleri geçersiz.", code="INVALID_REQUEST")
        operation = "CREATE_LINK"
        fields = self._call(
            operation,
            (
                source_module,
                source_absolute_number,
                link_module,
                target_module,
                target_absolute_number,
            ),
        )
        _expect(fields, 4, operation)
        return DoorsLink(_int(fields[0]), fields[1], fields[2], _int(fields[3]))

    def delete_link(
        self,
        source_module: str,
        source_absolute_number: int,
        link_module: str,
        target_module: str,
        target_absolute_number: int,
    ) -> None:
        if source_absolute_number < 1 or target_absolute_number < 1 or not link_module:
            raise DoorsConnectorError("Link parametreleri geçersiz.", code="INVALID_REQUEST")
        fields = self._call(
            "DELETE_LINK",
            (
                source_module,
                source_absolute_number,
                link_module,
                target_module,
                target_absolute_number,
            ),
        )
        _expect(fields, 0, "DELETE_LINK")
