from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, override_settings
from rest_framework.test import APITestCase

BASE = "/api/form-processes/numbering/"
FORMAT = {
    "code": "TEST",
    "name": "Test",
    "required_context": [{"key": "project", "required": True, "default": None, "max_length": 10}],
}


class FormNumberingTests(APITestCase):
    def setUp(self):
        preview = patch(
            "api.form_processes.numbering.client.preview_number", return_value="Test-UAV-001"
        )
        preview.start()
        self.addCleanup(preview.stop)
        self.user = get_user_model().objects.create_user(username="number-user", password="test")
        self.admin = get_user_model().objects.create_user(
            username="number-admin", password="test", is_staff=True
        )
        self.client.force_authenticate(self.admin)
        self.mapping_payload = {
            "template_code": "fm_dsg_0626",
            "target_field": "record_number",
            "format_code": "TEST",
            "enabled": True,
            "context_sources": {"project": {"source": "field", "field": "data.program"}},
        }

    def mapping(self):
        with patch("api.form_processes.numbering.client.get_format", return_value=FORMAT):
            response = self.client.post(BASE + "mappings/", self.mapping_payload, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        return response.data

    def generate(self, mapping, key="test-key", **changes):
        payload = {
            "mapping_id": mapping["id"],
            "form": {
                "template_code": "fm_dsg_0626",
                "record_number": "",
                "title": "Test form",
                "data": {"program": "UAV"},
                "notes": "",
            },
            "manual_context": {},
        }
        payload.update(changes)
        return self.client.post(
            BASE + "allocations/", payload, format="json", HTTP_IDEMPOTENCY_KEY=key
        )

    @patch("api.form_processes.numbering.client.generate_number")
    def test_generation_replay_and_persistent_locks(self, generate):
        generate.return_value = {"id": 42, "document_number": "Test-UAV-001"}
        mapping = self.mapping()
        with patch("api.form_processes.numbering.client.get_format", return_value=FORMAT):
            response = self.generate(mapping)
            self.assertEqual(response.status_code, 201, response.data)
            replay = self.generate(mapping)
        self.assertEqual(replay.status_code, 200, replay.data)
        self.assertEqual(generate.call_count, 1)
        record = response.data["record"]
        self.assertEqual(record["record_number"], "Test-UAV-001")
        self.assertEqual(record["status"], "draft")
        self.assertEqual(set(record["locked_fields"]), {"record_number", "data.program"})
        url = f"/api/form-processes/{record['id']}/"
        self.assertEqual(
            self.client.patch(url, {"data": {"program": "OTHER"}}, format="json").status_code, 400
        )
        unchanged = self.client.patch(
            url, {"record_number": "Test-UAV-001", "notes": "ok"}, format="json"
        )
        self.assertEqual(unchanged.status_code, 200, unchanged.data)
        self.assertEqual(unchanged.data["record_number"], "Test-UAV-001")

    def test_mapping_write_requires_admin(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(BASE + "mappings/", self.mapping_payload, format="json")
        self.assertEqual(response.status_code, 403)

    def test_invalid_target_and_cycle(self):
        self.mapping_payload["target_field"] = "data.program"
        with patch("api.form_processes.numbering.client.get_format", return_value=FORMAT):
            response = self.client.post(BASE + "mappings/", self.mapping_payload, format="json")
        self.assertEqual(response.status_code, 400)

    @patch("api.form_processes.numbering.client.generate_number")
    def test_missing_context_does_not_consume_number(self, generate):
        mapping = self.mapping()
        with patch("api.form_processes.numbering.client.get_format", return_value=FORMAT):
            response = self.generate(
                mapping, form={"template_code": "fm_dsg_0626", "title": "Test", "data": {}}
            )
        self.assertEqual(response.status_code, 400)
        generate.assert_not_called()

    @patch("api.form_processes.numbering.client.generate_number")
    def test_timeout_retry_uses_same_provider_key(self, generate):
        from .form_processes.numbering.client import NumberingUnavailable

        generate.side_effect = [NumberingUnavailable(), {"id": 43, "document_number": "NUM-2"}]
        mapping = self.mapping()
        with patch("api.form_processes.numbering.client.get_format", return_value=FORMAT):
            response = self.generate(mapping)
        self.assertEqual(response.status_code, 502, response.data)
        allocation_id = response.data["allocation_id"]
        retry = self.client.post(BASE + f"allocations/{allocation_id}/retry/", {}, format="json")
        self.assertEqual(retry.status_code, 200, retry.data)
        self.assertEqual(generate.call_args_list[0], generate.call_args_list[1])

    @patch(
        "api.form_processes.numbering.client.generate_number",
        return_value={"id": 43, "document_number": "NUM-2"},
    )
    def test_local_failure_retries_without_another_provider_call(self, generate):
        mapping = self.mapping()
        with (
            patch("api.form_processes.numbering.client.get_format", return_value=FORMAT),
            patch(
                "api.form_processes.services.lifecycle.FormProcessRecord.save",
                side_effect=RuntimeError("local failure"),
            ),
        ):
            response = self.generate(mapping)
        self.assertEqual(response.status_code, 502, response.data)
        retry = self.client.post(
            BASE + f"allocations/{response.data['allocation_id']}/retry/", {}, format="json"
        )
        self.assertEqual(retry.status_code, 200, retry.data)
        self.assertEqual(generate.call_count, 1)

    @patch(
        "api.form_processes.numbering.client.generate_number",
        return_value={"id": 43, "document_number": "NUM-2"},
    )
    def test_idempotency_conflict_and_disabled_mapping_replay(self, generate):
        mapping = self.mapping()
        with patch("api.form_processes.numbering.client.get_format", return_value=FORMAT):
            self.assertEqual(self.generate(mapping).status_code, 201)
        self.assertEqual(self.generate(mapping, manual_context={"extra": "x"}).status_code, 409)
        disabled = self.client.patch(
            BASE + f"mappings/{mapping['id']}/", {"enabled": False}, format="json"
        )
        self.assertEqual(disabled.status_code, 200, disabled.data)
        self.assertEqual(self.generate(mapping).status_code, 200)
        self.assertEqual(self.generate(mapping, key="new-request").status_code, 400)
        self.assertEqual(generate.call_count, 1)

    def test_invalid_template_and_non_scalar_field_source(self):
        with patch("api.form_processes.numbering.client.get_format", return_value=FORMAT):
            self.mapping_payload["template_code"] = "unknown"
            self.assertEqual(
                self.client.post(
                    BASE + "mappings/", self.mapping_payload, format="json"
                ).status_code,
                400,
            )
            self.mapping_payload["template_code"] = "fm_dsg_0626"
            self.mapping_payload["context_sources"]["project"]["field"] = []
            self.assertEqual(
                self.client.post(
                    BASE + "mappings/", self.mapping_payload, format="json"
                ).status_code,
                400,
            )

    @patch("api.form_processes.numbering.client.generate_number")
    def test_changed_format_and_overlength_context_are_rejected(self, generate):
        mapping = self.mapping()
        changed = {**FORMAT, "required_context": []}
        with patch("api.form_processes.numbering.client.get_format", return_value=changed):
            self.assertEqual(self.generate(mapping).status_code, 409)
        with patch("api.form_processes.numbering.client.get_format", return_value=FORMAT):
            response = self.generate(
                mapping,
                form={
                    "template_code": "fm_dsg_0626",
                    "title": "Test",
                    "data": {"program": "X" * 11},
                },
            )
            self.assertEqual(response.status_code, 400)
        generate.assert_not_called()

    @patch(
        "api.form_processes.numbering.client.generate_number",
        return_value={"id": 43, "document_number": "NUM-2"},
    )
    def test_fixed_manual_and_default_context(self, generate):
        for index, source in enumerate(
            [{"source": "fixed", "value": "FIXED"}, {"source": "manual"}, {"source": "default"}]
        ):
            with self.subTest(source=source):
                from .form_processes.models import FormNumberMapping

                FormNumberMapping.objects.filter(target_field="record_number").update(
                    target_field=f"data.unused_{index}"
                )
                contract = {
                    **FORMAT,
                    "required_context": [
                        {
                            "key": "project",
                            "required": False,
                            "default": "DEFAULT",
                            "max_length": 10,
                        }
                    ],
                }
                self.mapping_payload["context_sources"] = {"project": source}
                with patch("api.form_processes.numbering.client.get_format", return_value=contract):
                    response = self.client.post(
                        BASE + "mappings/", self.mapping_payload, format="json"
                    )
                    self.assertEqual(response.status_code, 201, response.data)
                    generate.return_value = {"id": 50 + index, "document_number": f"NUM-{index}"}
                    response = self.generate(
                        response.data,
                        key=f"source-{index}",
                        manual_context={"project": "MANUAL"}
                        if source["source"] == "manual"
                        else {},
                    )
                self.assertEqual(response.status_code, 201, response.data)
                expected = {
                    "fixed": {"project": "FIXED"},
                    "manual": {"project": "MANUAL"},
                    "default": {},
                }[source["source"]]
                self.assertEqual(generate.call_args.args[0]["context_data"], expected)

    @patch("api.form_processes.numbering.client.generate_number")
    def test_pending_allocation_is_private(self, generate):
        from .form_processes.numbering.client import NumberingUnavailable

        generate.side_effect = NumberingUnavailable()
        mapping = self.mapping()
        with patch("api.form_processes.numbering.client.get_format", return_value=FORMAT):
            response = self.generate(mapping)
        allocation_id = response.data["allocation_id"]
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.get(BASE + f"allocations/{allocation_id}/").status_code, 404)
        self.assertEqual(
            self.client.post(BASE + f"allocations/{allocation_id}/retry/").status_code, 404
        )

    @patch(
        "api.form_processes.numbering.client.generate_number",
        return_value={"id": 43, "document_number": "NUM-2"},
    )
    def test_delete_keeps_allocation_and_replay_does_not_recreate(self, generate):
        from .form_processes.models import FormNumberAllocation, FormProcessRecord

        mapping = self.mapping()
        with patch("api.form_processes.numbering.client.get_format", return_value=FORMAT):
            response = self.generate(mapping)
        self.assertEqual(
            self.client.delete(f"/api/form-processes/{response.data['record']['id']}/").status_code,
            204,
        )
        replay = self.generate(mapping)
        self.assertEqual(replay.status_code, 200)
        self.assertIsNone(replay.data["record"])
        self.assertEqual(FormProcessRecord.objects.count(), 0)
        self.assertEqual(FormNumberAllocation.objects.count(), 1)

    @patch("api.form_processes.numbering.client.generate_number")
    def test_concurrent_record_update_is_not_overwritten(self, generate):
        from .form_processes.models import FormProcessRecord

        record = FormProcessRecord.objects.create(
            process_code="others",
            template_code="fm_dsg_0626",
            record_number="MANUAL-1",
            title="Existing",
            data={"program": "UAV"},
        )
        self.mapping_payload["target_field"] = "data.ata_index"
        mapping = self.mapping()

        def change_during_request(*args):
            record.notes = "Concurrent edit"
            record.save()
            return {"id": 44, "document_number": "NUM-3"}

        generate.side_effect = change_during_request
        with patch("api.form_processes.numbering.client.get_format", return_value=FORMAT):
            response = self.generate(
                mapping,
                record_id=record.pk,
                expected_updated_at=record.updated_at.isoformat(),
                form={
                    "template_code": record.template_code,
                    "record_number": record.record_number,
                    "title": record.title,
                    "data": record.data,
                },
            )
        self.assertEqual(response.status_code, 409, response.data)
        record.refresh_from_db()
        self.assertEqual(record.notes, "Concurrent edit")
        self.assertNotIn("ata_index", record.data)

    def test_anonymous_and_inactive_users_cannot_read_mappings(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(BASE + "mappings/").status_code, 403)
        self.user.is_active = False
        self.user.save()
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.get(BASE + "mappings/").status_code, 403)

    @patch("api.form_processes.numbering.client.generate_number")
    def test_live_lease_blocks_second_attempt(self, generate):
        from datetime import timedelta

        from django.utils import timezone

        from .form_processes.models import FormNumberAllocation
        from .form_processes.numbering.client import NumberingUnavailable

        generate.side_effect = NumberingUnavailable()
        mapping = self.mapping()
        with patch("api.form_processes.numbering.client.get_format", return_value=FORMAT):
            response = self.generate(mapping)
        allocation = FormNumberAllocation.objects.get(pk=response.data["allocation_id"])
        allocation.lease_until = timezone.now() + timedelta(minutes=1)
        allocation.save()
        response = self.client.post(BASE + f"allocations/{allocation.pk}/retry/")
        self.assertEqual(response.status_code, 409)
        self.assertEqual(generate.call_count, 1)

    @patch(
        "api.form_processes.numbering.client.generate_number",
        return_value={"id": 43, "document_number": "NUM-2"},
    )
    def test_attachment_survives_failed_save_and_retry(self, generate):
        import json
        import tempfile
        from pathlib import Path

        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.test import override_settings

        from .form_processes.models import FormNumberAllocation
        from .test_form_processes import valid_pdf_bytes

        mapping = self.mapping()
        payload = {
            "mapping_id": mapping["id"],
            "form": {"template_code": "fm_dsg_0626", "title": "Test", "data": {"program": "UAV"}},
            "manual_context": {},
        }
        with tempfile.TemporaryDirectory() as directory, override_settings(MEDIA_ROOT=directory):
            with (
                patch("api.form_processes.numbering.client.get_format", return_value=FORMAT),
                patch(
                    "api.form_processes.services.lifecycle.FormProcessRecord.save",
                    side_effect=RuntimeError("save failed"),
                ),
            ):
                response = self.client.post(
                    BASE + "allocations/",
                    {
                        "payload": json.dumps(payload),
                        "attachment": SimpleUploadedFile(
                            "test.pdf", valid_pdf_bytes(), content_type="application/pdf"
                        ),
                    },
                    format="multipart",
                    HTTP_IDEMPOTENCY_KEY="attachment-test",
                )
            self.assertEqual(response.status_code, 502, response.data)
            allocation = FormNumberAllocation.objects.get(pk=response.data["allocation_id"])
            self.assertTrue(Path(allocation.attachment.path).exists())
            retry = self.client.post(BASE + f"allocations/{allocation.pk}/retry/")
            self.assertEqual(retry.status_code, 200, retry.data)
            self.assertEqual(retry.data["record"]["attachment_name"], "test.pdf")
            self.assertEqual(generate.call_count, 1)

    @patch(
        "api.form_processes.numbering.client.generate_number",
        return_value={"id": 43, "document_number": "  Mixed-001  "},
    )
    def test_generated_text_is_preserved_exactly(self, generate):
        self.mapping_payload["target_field"] = "data.ata_index"
        mapping = self.mapping()
        with patch("api.form_processes.numbering.client.get_format", return_value=FORMAT):
            response = self.generate(
                mapping,
                form={
                    "template_code": "fm_dsg_0626",
                    "record_number": "MANUAL",
                    "title": "Test",
                    "data": {"program": "UAV"},
                },
            )
        self.assertEqual(response.status_code, 201, response.data)
        record = response.data["record"]
        self.assertEqual(record["data"]["ata_index"], "  Mixed-001  ")
        updated = self.client.patch(
            f"/api/form-processes/{record['id']}/", {"notes": "New note"}, format="json"
        )
        self.assertEqual(updated.status_code, 200, updated.data)
        self.assertEqual(updated.data["data"]["ata_index"], "  Mixed-001  ")

    def test_cross_mapping_cycle_rolls_back(self):
        from .form_processes.models import FormNumberMapping

        self.mapping()
        self.mapping_payload["target_field"] = "data.program"
        self.mapping_payload["context_sources"] = {
            "project": {"source": "field", "field": "record_number"}
        }
        with patch("api.form_processes.numbering.client.get_format", return_value=FORMAT):
            response = self.client.post(BASE + "mappings/", self.mapping_payload, format="json")
        self.assertEqual(response.status_code, 400, response.data)
        self.assertEqual(FormNumberMapping.objects.count(), 1)

    @patch("api.form_processes.numbering.client.generate_number")
    def test_preview_checks_target_length_before_consuming_sequence(self, generate):
        mapping = self.mapping()
        with (
            patch("api.form_processes.numbering.client.get_format", return_value=FORMAT),
            patch("api.form_processes.numbering.client.preview_number", return_value="X" * 129),
        ):
            response = self.generate(mapping)
        self.assertEqual(response.status_code, 400, response.data)
        generate.assert_not_called()

    @patch("api.form_processes.numbering.client.generate_number")
    def test_archived_record_and_filled_target_are_rejected(self, generate):
        from .form_processes.models import FormProcessRecord

        self.mapping_payload["target_field"] = "data.ata_index"
        mapping = self.mapping()
        record = FormProcessRecord.objects.create(
            process_code="others",
            template_code="fm_dsg_0626",
            record_number="ARCHIVE",
            title="Archived",
            status="archived",
            data={"program": "UAV"},
        )
        response = self.generate(
            mapping,
            record_id=record.pk,
            expected_updated_at=record.updated_at.isoformat(),
            form={
                "template_code": record.template_code,
                "record_number": record.record_number,
                "title": record.title,
                "data": record.data,
            },
        )
        self.assertEqual(response.status_code, 409, response.data)
        response = self.generate(
            mapping,
            form={
                "template_code": record.template_code,
                "record_number": "NEW",
                "title": "New",
                "data": {"program": "UAV", "ata_index": "Existing"},
            },
        )
        self.assertEqual(response.status_code, 400, response.data)
        generate.assert_not_called()


@override_settings(
    NUMARATOR_BASE_URL="https://numarator.example.test",
    NUMARATOR_API_KEY="test-placeholder",
    NUMARATOR_TIMEOUT=15,
)
class NumberingClientTests(SimpleTestCase):
    @patch("api.form_processes.numbering.client.build_opener")
    def test_server_headers_timeout_and_response(self, build_opener):
        from .form_processes.numbering import client

        response = MagicMock()
        response.read.return_value = (
            b'{"success":true,"data":{"id":1,"document_number":"Mixed-001"}}'
        )
        build_opener.return_value.open.return_value.__enter__.return_value = response
        result = client.generate_number(
            {"format_code": "TEST", "context_data": {}}, "form-operation"
        )
        self.assertEqual(result, {"id": 1, "document_number": "Mixed-001"})
        req = build_opener.return_value.open.call_args.args[0]
        self.assertEqual(req.full_url, "https://numarator.example.test/api/private/v1/numbers/")
        self.assertEqual(req.get_header("X-api-key"), "test-placeholder")
        self.assertEqual(req.get_header("Idempotency-key"), "form-operation")
        self.assertEqual(build_opener.return_value.open.call_args.kwargs["timeout"], 15)
        self.assertIsNone(
            client.NoRedirect().redirect_request(None, None, 302, None, None, "https://other.test")
        )

    @patch("api.form_processes.numbering.client.build_opener")
    def test_provider_errors_are_redacted(self, build_opener):
        from urllib.error import URLError

        from .form_processes.numbering import client

        build_opener.return_value.open.side_effect = URLError("private-service-details")
        with self.assertRaises(client.NumberingUnavailable) as caught:
            client.get_format("TEST")
        self.assertNotIn("private-service-details", str(caught.exception))

    def test_malformed_context_contract_is_rejected(self):
        from .form_processes.numbering import client

        with self.assertRaises(client.NumberingUnavailable):
            client.validate_format(
                {"code": "TEST", "required_context": [{"key": "p", "max_length": "wrong"}]}
            )
