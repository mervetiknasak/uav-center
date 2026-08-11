from io import BytesIO
from tempfile import NamedTemporaryFile, TemporaryDirectory
from unittest.mock import patch
from zipfile import ZIP_DEFLATED, ZipFile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from .models import Document
from .services.document_extractor import extract_document
from .services.document_limits import DocumentPreflightError, preflight_document


def office_archive(extension: str = ".docx", *, payload: bytes = b"document") -> bytes:
    required_part = {
        ".docx": "word/document.xml",
        ".xlsx": "xl/workbook.xml",
        ".pptx": "ppt/presentation.xml",
    }[extension]
    content = BytesIO()
    with ZipFile(content, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", b"types")
        archive.writestr(required_part, payload)
    return content.getvalue()


class DocumentPreflightTests(SimpleTestCase):
    def test_office_preflight_restores_caller_owned_cursor(self):
        source = BytesIO(office_archive())
        source.seek(5)

        preflight_document(source, ".docx")

        self.assertEqual(source.tell(), 5)

    @override_settings(DOCUMENT_MAX_ARCHIVE_ENTRIES=1)
    def test_office_preflight_rejects_excessive_archive_entries(self):
        with self.assertRaisesMessage(DocumentPreflightError, "arşiv öğesi sınırını"):
            preflight_document(BytesIO(office_archive()), ".docx")

    @override_settings(DOCUMENT_MAX_UNCOMPRESSED_SIZE=10)
    def test_office_preflight_rejects_excessive_expanded_size(self):
        with self.assertRaisesMessage(DocumentPreflightError, "açıldığında"):
            preflight_document(
                BytesIO(office_archive(payload=b"x" * 20)),
                ".docx",
            )

    def test_office_preflight_requires_format_specific_ooxml_part(self):
        content = BytesIO()
        with ZipFile(content, "w", compression=ZIP_DEFLATED) as archive:
            archive.writestr("[Content_Types].xml", b"types")
            archive.writestr("unrelated.xml", b"content")

        with self.assertRaisesMessage(DocumentPreflightError, "geçerli bir OOXML"):
            preflight_document(BytesIO(content.getvalue()), ".docx")

    @override_settings(DOCUMENT_MAX_PDF_PAGES=1)
    def test_pdf_preflight_rejects_excessive_page_count(self):
        from pypdf import PdfWriter

        content = BytesIO()
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        writer.add_blank_page(width=100, height=100)
        writer.write(content)

        with self.assertRaisesMessage(DocumentPreflightError, "sayfa sınırını"):
            preflight_document(BytesIO(content.getvalue()), ".pdf")

    @override_settings(DOCUMENT_MAX_PDF_PAGES=1)
    def test_pdf_extractor_reapplies_page_limit_in_worker_boundary(self):
        from pypdf import PdfWriter

        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        writer.add_blank_page(width=100, height=100)
        with NamedTemporaryFile(suffix=".pdf") as pdf_file:
            writer.write(pdf_file)
            pdf_file.flush()

            with self.assertRaisesMessage(DocumentPreflightError, "sayfa sınırını"):
                extract_document(pdf_file.name, use_ocr=False)

    @override_settings(OCR_MAX_PIXELS=100)
    def test_image_preflight_rejects_pixel_limit_before_ocr(self):
        from PIL import Image

        content = BytesIO()
        Image.new("RGB", (11, 11), "white").save(content, format="PNG")

        with self.assertRaisesMessage(DocumentPreflightError, "izin verilen sınır"):
            preflight_document(BytesIO(content.getvalue()), ".png")

    @override_settings(OCR_MAX_PIXELS=100)
    @patch("api.services.document_extractor.read_image")
    def test_extractor_rejects_oversized_image_before_pixel_copy(self, read_image):
        from PIL import Image

        content = BytesIO()
        Image.new("RGB", (11, 11), "white").save(content, format="PNG")
        with NamedTemporaryFile(suffix=".png") as image_file:
            image_file.write(content.getvalue())
            image_file.flush()

            with self.assertRaises(DocumentPreflightError):
                extract_document(image_file.name, use_ocr=True)

        read_image.assert_not_called()


class DocumentUploadPreflightApiTests(TestCase):
    def setUp(self):
        self.media_directory = TemporaryDirectory()
        self.settings_override = override_settings(MEDIA_ROOT=self.media_directory.name)
        self.settings_override.enable()
        user = get_user_model().objects.create_user(
            username="preflight-user",
            password="StrongPass123!",
        )
        self.client.force_login(user)

    def tearDown(self):
        self.settings_override.disable()
        self.media_directory.cleanup()

    def test_invalid_ooxml_is_rejected_before_document_or_job_is_created(self):
        response = self.client.post(
            reverse("document-upload"),
            data={
                "file": SimpleUploadedFile(
                    "not-a-document.docx",
                    b"not a zip archive",
                    content_type=(
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    ),
                ),
                "prompt": "",
                "use_ai": "false",
                "use_ocr": "false",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("file", response.json())
        self.assertEqual(Document.objects.count(), 0)
