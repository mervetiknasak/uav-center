from io import BytesIO
from zipfile import ZipFile

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase
from docx import Document
from docx.oxml.ns import qn
from docxtpl import DocxTemplate
from rest_framework.test import APITestCase

from .form_processes.catalog import (
    FORM_TEMPLATES,
    FormTemplateValidationError,
    form_process_catalog,
    validate_form_data,
)
from .models import FormProcessRecord


class FormProcessCatalogTests(SimpleTestCase):
    def test_catalog_contains_every_retained_fm_docx(self):
        catalog = form_process_catalog()

        self.assertEqual(len(catalog), 13)
        self.assertEqual(len(FORM_TEMPLATES), 35)
        self.assertEqual(len({template.code for template in FORM_TEMPLATES}), 35)
        for template in FORM_TEMPLATES:
            with self.subTest(template=template.code):
                self.assertTrue(template.document_path.is_file())
                DocxTemplate(template.document_path)
                self.assertTrue(template.fields)

    def test_catalog_does_not_request_signatures_or_signature_dates(self):
        banned_terms = ("imza", "signature", "signer")
        schema_terms = []
        for template in FORM_TEMPLATES:
            schema_terms.extend((template.title, template.description))
            for field in template.fields:
                schema_terms.extend((field.key, field.label))
                for column in field.columns:
                    schema_terms.extend((column.key, column.label))
            retained_template = DocxTemplate(template.document_path)
            schema_terms.extend(retained_template.get_undeclared_template_variables())

        for term in schema_terms:
            with self.subTest(term=term):
                normalized = term.casefold()
                self.assertFalse(any(banned in normalized for banned in banned_terms))

    def test_removed_signature_fields_are_rejected(self):
        removed_fields_by_template = {
            "fm_dsg_0008e": {
                "employee_signature": "Eski imza girdisi",
                "employee_signature_date": "2026-08-17",
            },
            "fm_dsg_0308e": {"signature_date": "2026-08-17"},
            "fm_dsg_0327": {
                "product_head_date": "2026-08-17",
                "srb_manager_date": "2026-08-17",
            },
        }

        for template_code, data in removed_fields_by_template.items():
            with self.subTest(template=template_code):
                with self.assertRaises(FormTemplateValidationError) as raised:
                    validate_form_data(template_code, data, require_required=False)
                self.assertIn("data", raised.exception.errors)


class FormProcessApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="form-process-user",
            password="test-password",
            is_active=True,
        )
        self.client.force_authenticate(self.user)

    def panel_payload(self, **overrides):
        payload = {
            "template_code": "fm_dsg_0200t",
            "record_number": "panel-2026-001",
            "title": "Uçuş Kontrol Panel Uyum Beyanı",
            "status": "in_review",
            "data": {
                "panel_name": "Uçuş Kontrol Paneli",
                "project_name": "İHA-X",
                "related_documents": "Sistem Sertifikasyon Planı",
                "compliance_documents": "Uyum Matrisi Rev. 2",
                "certification_actions": "Aksiyon bulunmuyor.",
                "declaration": "Panel kapsamındaki gereksinimler karşılanmıştır.",
                "configuration_basis": "Konfigürasyon C-14",
                "panel_coordinator": "Ayşe Yılmaz",
                "panel_members": "Mehmet Kaya",
                "declaration_date": "2026-08-13",
            },
            "notes": "Kurul incelemesine hazır.",
        }
        payload.update(overrides)
        return payload

    def fcc_payload(self, **overrides):
        payload = {
            "template_code": "fm_dsg_0327",
            "record_number": "fcc-2026-001",
            "title": "ANKA Uçuş Uygunluk Belgesi",
            "status": "approved",
            "data": {
                "project_name": "ANKA III",
                "aircraft_type": "İHA",
                "aircraft_model": "ANKA-3 Block A",
                "aircraft_serial_number": "T-001",
                "flight_clearance_reference": "TFCC-01.00",
                "clearance_type": "initial",
                "request_reason": "İlk uçuş ve takip eden geliştirme uçuşları.",
                "request_reason_continued": "Test sahası operasyonları ile sınırlıdır.",
                "valid_from": "2026-08-17",
                "valid_until": "2026-09-30",
                "aircraft_limitation_document_reference": "ALD-ANKA3-001 Rev A",
                "product_head_name": "Ayşe Yılmaz",
                "srb_manager_name": "Mehmet Kaya",
                "statement_of_conformity_reference": "SOC-ANKA3-001",
                "flight_conditions_application_reference": "FCA-ANKA3-001",
                "aircraft_configuration_reference": "ASR-ANKA3-014",
                "airworthiness_safety_summary_documents": "AWSS-001 Rev B\nFSES-004 Rev A",
                "itinerary_airspace_restrictions_reference": "ROUTE-RPT-003",
                "flight_crew_qualification_reference": "FTOM Rev 12",
                "passenger_carrying_restrictions_reference": "OPS-LIM-008",
                "afm_reference": "AFM-ANKA3-DRAFT",
                "flight_test_procedure_reference": "FTP-ANKA3-021",
                "continuing_airworthiness_reference": "ICA-ANKA3-002",
                "clearance_change_criteria_reference": "FCC-CRIT-001",
                "other_appendix": "Silah sistemi emniyet değerlendirmesi WSSA-07.",
                "issue_records": [
                    {
                        "issue": "TFCC-01.00",
                        "date": "2026-08-17",
                        "prepared_by": "Selin Demir",
                        "description": "İlk yayın",
                    }
                ],
            },
            "notes": "SRB kararı ile yayımlandı.",
        }
        payload.update(overrides)
        return payload

    def test_catalog_requires_active_authentication(self):
        response = self.client.get("/api/form-processes/templates/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 13)
        self.assertEqual(
            sum(len(process["templates"]) for process in response.data),
            35,
        )

        self.client.force_authenticate(user=None)
        unauthorized = self.client.get("/api/form-processes/templates/")
        self.assertIn(unauthorized.status_code, {401, 403})

    def test_create_list_update_and_delete_shared_record(self):
        create_response = self.client.post(
            "/api/form-processes/",
            self.panel_payload(),
            format="json",
        )

        self.assertEqual(create_response.status_code, 201)
        self.assertEqual(create_response.data["process_code"], "panel-declaration")
        self.assertEqual(create_response.data["record_number"], "PANEL-2026-001")
        self.assertEqual(create_response.data["process_name"], "Panel Uyum Beyanı")
        self.assertEqual(create_response.data["form_number"], "FM.DSG.0200T")
        self.assertEqual(FormProcessRecord.objects.get().created_by, self.user)

        update_response = self.client.patch(
            f"/api/form-processes/{create_response.data['id']}/",
            {"status": "approved", "notes": "Onaylandı."},
            format="json",
        )
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(update_response.data["status_display"], "Onaylandı")

        list_response = self.client.get("/api/form-processes/?process=panel-declaration")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.data), 1)

        delete_response = self.client.delete(f"/api/form-processes/{create_response.data['id']}/")
        self.assertEqual(delete_response.status_code, 204)
        self.assertFalse(FormProcessRecord.objects.exists())

    def test_shared_record_is_visible_to_active_users_but_not_inactive_users(self):
        create_response = self.client.post(
            "/api/form-processes/",
            self.panel_payload(),
            format="json",
        )
        record_url = f"/api/form-processes/{create_response.data['id']}/"
        other_active_user = get_user_model().objects.create_user(
            username="other-form-process-user",
            password="test-password",
            is_active=True,
        )
        self.client.force_authenticate(other_active_user)

        shared_response = self.client.get(record_url)

        self.assertEqual(shared_response.status_code, 200)
        self.assertEqual(shared_response.data["record_number"], "PANEL-2026-001")

        inactive_user = get_user_model().objects.create_user(
            username="inactive-form-process-user",
            password="test-password",
            is_active=False,
        )
        self.client.force_authenticate(inactive_user)

        inactive_response = self.client.get(record_url)

        self.assertEqual(inactive_response.status_code, 403)

    def test_rejects_missing_unknown_and_invalid_template_fields(self):
        missing_required = self.client.post(
            "/api/form-processes/",
            self.panel_payload(data={}, status="approved"),
            format="json",
        )
        self.assertEqual(missing_required.status_code, 400)
        self.assertIn("panel_name", missing_required.data)

        unknown_field = self.client.post(
            "/api/form-processes/",
            self.panel_payload(
                record_number="PANEL-2026-002",
                data={**self.panel_payload()["data"], "unexpected": "secret"},
            ),
            format="json",
        )
        self.assertEqual(unknown_field.status_code, 400)
        self.assertIn("data", unknown_field.data)

        invalid_date = self.client.post(
            "/api/form-processes/",
            self.panel_payload(
                record_number="PANEL-2026-003",
                data={**self.panel_payload()["data"], "declaration_date": "13/08/2026"},
            ),
            format="json",
        )
        self.assertEqual(invalid_date.status_code, 400)
        self.assertIn("declaration_date", invalid_date.data)
        self.assertFalse(FormProcessRecord.objects.exists())

    def test_draft_allows_missing_required_fields_but_keeps_shape_validation(self):
        draft = self.client.post(
            "/api/form-processes/",
            self.panel_payload(data={}, status="draft"),
            format="json",
        )

        self.assertEqual(draft.status_code, 201)
        self.assertEqual(draft.data["status"], "draft")
        self.assertEqual(draft.data["data"]["panel_name"], "")

        invalid_date = self.client.post(
            "/api/form-processes/",
            self.panel_payload(
                record_number="PANEL-2026-002",
                status="draft",
                data={"declaration_date": "13/08/2026"},
            ),
            format="json",
        )
        self.assertEqual(invalid_date.status_code, 400)
        self.assertIn("declaration_date", invalid_date.data)

        unknown_field = self.client.post(
            "/api/form-processes/",
            self.panel_payload(
                record_number="PANEL-2026-003",
                status="draft",
                data={"unexpected": "value"},
            ),
            format="json",
        )
        self.assertEqual(unknown_field.status_code, 400)
        self.assertIn("data", unknown_field.data)

    def test_fcc_validates_structured_issue_records(self):
        created = self.client.post(
            "/api/form-processes/",
            self.fcc_payload(),
            format="json",
        )
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.data["data"]["issue_records"][0]["issue"], "TFCC-01.00")

        invalid_data = {
            **self.fcc_payload()["data"],
            "issue_records": [
                {
                    "issue": "TFCC-01.01",
                    "date": "17/08/2026",
                    "prepared_by": "Selin Demir",
                    "description": "Revizyon",
                }
            ],
        }
        invalid = self.client.post(
            "/api/form-processes/",
            self.fcc_payload(record_number="FCC-2026-002", data=invalid_data),
            format="json",
        )
        self.assertEqual(invalid.status_code, 400)
        self.assertIn("issue_records", invalid.data)

        invalid_period = self.client.post(
            "/api/form-processes/",
            self.fcc_payload(
                record_number="FCC-2026-003",
                data={
                    **self.fcc_payload()["data"],
                    "valid_from": "2026-09-30",
                    "valid_until": "2026-08-17",
                },
            ),
            format="json",
        )
        self.assertEqual(invalid_period.status_code, 400)
        self.assertIn("valid_until", invalid_period.data)

    def test_approval_requires_complete_data_and_template_is_immutable(self):
        draft = self.client.post(
            "/api/form-processes/",
            self.panel_payload(data={}, status="draft"),
            format="json",
        )
        record_url = f"/api/form-processes/{draft.data['id']}/"

        incomplete_approval = self.client.patch(record_url, {"status": "approved"}, format="json")
        self.assertEqual(incomplete_approval.status_code, 400)
        self.assertIn("panel_name", incomplete_approval.data)

        template_change = self.client.patch(
            record_url,
            {"template_code": "fm_dsg_0328"},
            format="json",
        )
        self.assertEqual(template_change.status_code, 400)
        self.assertIn("template_code", template_change.data)

    def test_approved_record_can_be_archived_and_reopened_as_draft(self):
        created = self.client.post("/api/form-processes/", self.panel_payload(), format="json")
        record_url = f"/api/form-processes/{created.data['id']}/"

        archived = self.client.patch(record_url, {"status": "archived"}, format="json")
        self.assertEqual(archived.status_code, 200)
        self.assertEqual(archived.data["status"], "archived")

        reopened = self.client.patch(record_url, {"status": "draft"}, format="json")
        self.assertEqual(reopened.status_code, 200)
        self.assertEqual(reopened.data["status"], "draft")

    def test_removed_fcc_signature_dates_are_rejected(self):
        response = self.client.post(
            "/api/form-processes/",
            self.fcc_payload(
                data={
                    **self.fcc_payload()["data"],
                    "product_head_date": "2026-08-17",
                    "srb_manager_date": "2026-08-17",
                }
            ),
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("data", response.data)

    def test_record_number_is_unique_within_process(self):
        first = self.client.post("/api/form-processes/", self.panel_payload(), format="json")
        duplicate = self.client.post(
            "/api/form-processes/",
            self.panel_payload(title="İkinci kayıt"),
            format="json",
        )

        self.assertEqual(first.status_code, 201)
        self.assertEqual(duplicate.status_code, 400)
        self.assertIn("record_number", duplicate.data)

    def test_generates_word_document_from_retained_template_and_validated_data(self):
        create_response = self.client.post(
            "/api/form-processes/",
            self.panel_payload(),
            format="json",
        )

        response = self.client.get(
            f"/api/form-processes/{create_response.data['id']}/generated-document/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        generated_bytes = b"".join(response.streaming_content)
        generated = Document(BytesIO(generated_bytes))
        text_parts = [paragraph.text for paragraph in generated.paragraphs]
        for table in generated.tables:
            text_parts.extend(cell.text for row in table.rows for cell in row.cells)
        generated_text = "\n".join(text_parts)
        self.assertIn("PANEL UYUM BEYANI", generated_text.upper())
        self.assertIn("SÜREÇ KAYIT BİLGİLERİ", generated_text)
        self.assertIn("Uçuş Kontrol Paneli", generated_text)
        self.assertIn("PANEL-2026-001", generated_text)
        self.assertNotIn("{{", generated_text)
        with ZipFile(BytesIO(generated_bytes)) as package:
            self.assertIn("word/document.xml", package.namelist())

    def test_generates_fcc_document_from_authoritative_template(self):
        created = self.client.post(
            "/api/form-processes/",
            self.fcc_payload(),
            format="json",
        )
        self.assertEqual(created.status_code, 201)

        response = self.client.get(f"/api/form-processes/{created.data['id']}/generated-document/")
        self.assertEqual(response.status_code, 200)
        generated_bytes = b"".join(response.streaming_content)
        generated = Document(BytesIO(generated_bytes))
        text_parts = [node.text or "" for node in generated._element.iter(qn("w:t"))]
        for section in generated.sections:
            for header in (section.header, section.first_page_header):
                text_parts.extend(node.text or "" for node in header._element.iter(qn("w:t")))
        generated_text = "".join(text_parts)

        self.assertIn("FLIGHT CLEARANCE CERTIFICATE", generated_text)
        self.assertIn("ANKA III", generated_text)
        self.assertIn("T-001", generated_text)
        self.assertIn("SOC-ANKA3-001", generated_text)
        self.assertIn("17.08.2026", generated_text)
        self.assertIn("TFCC-01.00", generated_text)
        self.assertIn("☒", generated_text)
        self.assertNotIn("{{", generated_text)
        self.assertNotIn("e.g. First Flight", generated_text)
        self.assertNotIn("This Section should contain", generated_text)
        signature_table = generated.tables[3].rows[1].cells[0].tables[0]
        self.assertEqual(signature_table.rows[1].cells[0].text.strip(), "Date:")
        self.assertEqual(signature_table.rows[1].cells[1].text.strip(), "Date:")
