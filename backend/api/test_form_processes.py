from io import BytesIO
from zipfile import ZipFile

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase
from docx import Document
from docxtpl import DocxTemplate
from rest_framework.test import APITestCase

from .form_processes.catalog import FORM_TEMPLATES, form_process_catalog
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
            self.panel_payload(data={}),
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
