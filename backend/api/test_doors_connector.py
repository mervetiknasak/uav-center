import tempfile
from pathlib import Path
from unittest import TestCase

from .services.doors_connector import (
    PROTOCOL_VERSION,
    DoorsConfig,
    DoorsConnector,
    DoorsConnectorError,
    OleAutomationTransport,
    _hex_decode,
    _hex_encode,
    _read_response,
    _write_request,
)


class FakeTransport:
    def __init__(self, responses=None):
        self.responses = responses or {}
        self.calls = []

    def call(self, operation, arguments):
        self.calls.append((operation, list(arguments)))
        response = self.responses.get(operation, [])
        if isinstance(response, Exception):
            raise response
        return list(response)


class FakeAutomation:
    def __init__(self, fields):
        self.Result = ""
        self.fields = fields
        self.run_file = None

    def runFile(self, dxl_file_name):
        self.run_file = dxl_file_name
        request_lines = Path(self.Result).read_text(encoding="ascii").splitlines()
        response_path = Path(_hex_decode(request_lines[0]))
        lines = [PROTOCOL_VERSION, "OK", str(len(self.fields))]
        lines.extend(_hex_encode(field) for field in self.fields)
        response_path.write_text("\n".join(lines) + "\n", encoding="ascii")
        self.Result = f"{PROTOCOL_VERSION}:OK"


class DoorsProtocolTests(TestCase):
    def test_hex_round_trip_preserves_unicode_and_control_characters(self):
        value = "İHA gereksinimi\n%00\t🚁"

        self.assertEqual(_hex_decode(_hex_encode(value)), value)

    def test_request_is_ascii_and_contains_no_raw_dxl_payload(self):
        with tempfile.TemporaryDirectory() as directory:
            request = Path(directory) / "request"
            response = Path(directory) / "response"

            _write_request(request, response, "UPDATE_OBJECT", ["/Proje/Modül", 'x"; halt'])

            text = request.read_text(encoding="ascii")
            self.assertNotIn("/Proje/Modül", text)
            self.assertNotIn("halt", text)
            self.assertEqual(text.splitlines()[1], PROTOCOL_VERSION)

    def test_error_response_is_normalized(self):
        with tempfile.TemporaryDirectory() as directory:
            response = Path(directory) / "response"
            response.write_text(
                "\n".join(
                    [
                        PROTOCOL_VERSION,
                        "ERR",
                        "2",
                        _hex_encode("OBJECT_NOT_FOUND"),
                        _hex_encode("Nesne yok"),
                    ]
                )
                + "\n",
                encoding="ascii",
            )

            with self.assertRaises(DoorsConnectorError) as context:
                _read_response(response, "GET_OBJECT")

            self.assertEqual(context.exception.code, "OBJECT_NOT_FOUND")
            self.assertEqual(context.exception.operation, "GET_OBJECT")

    def test_response_field_count_is_strict(self):
        with tempfile.TemporaryDirectory() as directory:
            response = Path(directory) / "response"
            response.write_text(
                f"{PROTOCOL_VERSION}\nOK\n2\n{_hex_encode('only-one')}\n",
                encoding="ascii",
            )

            with self.assertRaises(DoorsConnectorError) as context:
                _read_response(response, "PING")

            self.assertEqual(context.exception.code, "INVALID_RESPONSE")


class OleAutomationTransportTests(TestCase):
    def test_transport_uses_result_runfile_and_response_file(self):
        with tempfile.TemporaryDirectory() as directory:
            bridge = Path(directory) / "bridge.dxl"
            bridge.write_text("// test bridge", encoding="utf-8")
            automation = FakeAutomation(["DXLC/1", "Veritabanı", "pilot", "pilot", "host", "WIN32"])
            transport = OleAutomationTransport(
                DoorsConfig(bridge_path=bridge.resolve(), temp_dir=Path(directory), lock_timeout=1),
                automation=automation,
            )

            fields = transport.call("PING", [])

            self.assertEqual(fields[1], "Veritabanı")
            self.assertEqual(automation.run_file, str(bridge.resolve()))

    def test_transport_rejects_missing_completion_marker(self):
        class IncompleteAutomation:
            Result = ""

            def runFile(self, _):
                return None

        with tempfile.TemporaryDirectory() as directory:
            bridge = Path(directory) / "bridge.dxl"
            bridge.write_text("// test bridge", encoding="utf-8")
            transport = OleAutomationTransport(
                DoorsConfig(bridge_path=bridge.resolve(), temp_dir=Path(directory), lock_timeout=1),
                automation=IncompleteAutomation(),
            )

            with self.assertRaises(DoorsConnectorError) as context:
                transport.call("PING", [])

            self.assertEqual(context.exception.code, "BRIDGE_NOT_COMPLETED")


class DoorsConnectorTests(TestCase):
    def test_ping_maps_verified_server_fields(self):
        transport = FakeTransport({"PING": ["DXLC/1", "UAV", "Ada", "ada", "doors-host", "WIN32"]})

        info = DoorsConnector(transport=transport).check_connection()

        self.assertEqual(info.database_name, "UAV")
        self.assertEqual(info.doors_user, "Ada")

    def test_list_objects_maps_paging_and_unreadable_attributes(self):
        transport = FakeTransport(
            {
                "LIST_OBJECTS": [
                    "1",
                    "11",
                    "1",
                    "42",
                    "SYS-42",
                    "2.1",
                    "2",
                    "1",
                    "Başlık",
                    "0",
                    "",
                ]
            }
        )
        connector = DoorsConnector(transport=transport)

        page = connector.list_objects(
            "/UAV/Gereksinimler",
            attributes=["Object Heading", "Gizli"],
            offset=10,
            limit=1,
        )

        self.assertTrue(page.has_more)
        self.assertEqual(page.next_offset, 11)
        self.assertEqual(page.items[0].absolute_number, 42)
        self.assertEqual(page.items[0].attributes["Object Heading"], "Başlık")
        self.assertIsNone(page.items[0].attributes["Gizli"])

    def test_update_object_normalizes_values_and_uses_fixed_operation(self):
        transport = FakeTransport({"UPDATE_OBJECT": ["7", "REQ-7", "1.2", "2"]})
        connector = DoorsConnector(transport=transport)

        result = connector.update_object(
            "/UAV/Gereksinimler",
            7,
            {"Object Heading": "Kontrol", "Approved": True},
        )

        self.assertEqual(result.identifier, "REQ-7")
        operation, arguments = transport.calls[0]
        self.assertEqual(operation, "UPDATE_OBJECT")
        self.assertEqual(arguments[0:3], ["/UAV/Gereksinimler", "7", "2"])
        self.assertEqual(arguments[-2:], ["BOOLEAN", "1"])

    def test_arbitrary_operation_is_not_exposed_by_connector(self):
        connector = DoorsConnector(transport=FakeTransport())

        self.assertFalse(hasattr(connector, "run_dxl"))
        self.assertFalse(hasattr(connector, "run_str"))

    def test_page_limit_is_bounded(self):
        connector = DoorsConnector(transport=FakeTransport())

        with self.assertRaises(DoorsConnectorError) as context:
            connector.list_objects("/UAV/Reqs", limit=1001)

        self.assertEqual(context.exception.code, "INVALID_REQUEST")


class DxlBridgeStaticSafetyTests(TestCase):
    def setUp(self):
        self.bridge = (
            Path(__file__).parent / "services" / "dxl" / "doors_connector_bridge.dxl"
        ).read_text(encoding="utf-8")

    def test_bridge_has_no_dynamic_code_execution_or_os_command(self):
        source_without_comments = "\n".join(
            line for line in self.bridge.splitlines() if not line.lstrip().startswith("*")
        )

        self.assertNotIn("eval(", source_without_comments)
        self.assertNotIn("evalTop", source_without_comments)
        self.assertNotIn("system(", source_without_comments)
        self.assertNotIn("runStr", source_without_comments)

    def test_bridge_dispatches_only_documented_fixed_operations(self):
        expected = {
            "PING",
            "LIST_ITEMS",
            "GET_MODULE",
            "LIST_ATTRIBUTES",
            "LIST_OBJECTS",
            "GET_OBJECT",
            "GET_MODULE_ATTRIBUTES",
            "CREATE_FOLDER",
            "CREATE_FORMAL_MODULE",
            "CREATE_OBJECT",
            "UPDATE_OBJECT",
            "UPDATE_MODULE_ATTRIBUTES",
            "SOFT_DELETE_OBJECT",
            "LIST_OUTGOING_LINKS",
            "CREATE_LINK",
            "DELETE_LINK",
        }

        for operation in expected:
            self.assertIn(f'operation == "{operation}"', self.bridge)
