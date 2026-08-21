from types import SimpleNamespace

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse

from .admin import ReadOnlyAdmin, TechnicalDocumentAdmin, TechnicalDocumentAdminForm
from .documents.models import (
    AnalysisControl,
    Document,
    DocumentAnalysisRun,
    DocumentChunk,
)
from .edk.models import EDKApplication
from .form_processes.models import FormProcessRecord
from .jobs.models import AsyncJob
from .organization.models import (
    PanelResponsible,
    Person,
    PersonGroup,
    Project,
    ProjectPanel,
)
from .technical_documents.models import (
    CoverPage,
    TechnicalDocument,
    TechnicalDocumentNotification,
    TechnicalDocumentStatusHistory,
)


class ApplicationAdminTests(TestCase):
    editable_models = {
        AnalysisControl,
        CoverPage,
        PanelResponsible,
        Person,
        PersonGroup,
        Project,
        ProjectPanel,
        TechnicalDocument,
    }
    read_only_models = {
        AsyncJob,
        Document,
        DocumentAnalysisRun,
        DocumentChunk,
        EDKApplication,
        FormProcessRecord,
        TechnicalDocumentNotification,
        TechnicalDocumentStatusHistory,
    }

    @classmethod
    def setUpTestData(cls):
        cls.admin_user = get_user_model().objects.create_superuser(
            username="admin-test",
            email="admin@example.com",
            password="test-password",
        )

    def setUp(self):
        self.client.force_login(self.admin_user)
        self.request = RequestFactory().get("/admin/")
        self.request.user = self.admin_user

    def test_all_application_models_are_registered(self):
        registered_models = self.editable_models | self.read_only_models

        self.assertTrue(registered_models.issubset(admin.site._registry))

    def test_operational_and_audit_models_are_view_only(self):
        for model in self.read_only_models:
            with self.subTest(model=model.__name__):
                model_admin = admin.site._registry[model]
                self.assertIsInstance(model_admin, ReadOnlyAdmin)
                self.assertTrue(model_admin.has_view_permission(self.request))
                self.assertFalse(model_admin.has_add_permission(self.request))
                self.assertFalse(model_admin.has_change_permission(self.request))
                self.assertFalse(model_admin.has_delete_permission(self.request))

    def test_every_application_changelist_renders(self):
        for model in self.editable_models | self.read_only_models:
            with self.subTest(model=model.__name__):
                url = reverse(f"admin:{model._meta.app_label}_{model._meta.model_name}_changelist")
                response = self.client.get(url)

                self.assertEqual(response.status_code, 200)

    def test_technical_document_admin_records_status_changes(self):
        project = Project.objects.create(name="Test Projesi", code="TP")
        document = TechnicalDocument.objects.create(
            project=project,
            code="TD-001",
            title="Test Dokümanı",
            status=TechnicalDocument.STATUS_DRAFT,
            created_by=self.admin_user,
            updated_by=self.admin_user,
        )
        document.status = TechnicalDocument.STATUS_IN_REVIEW
        model_admin = TechnicalDocumentAdmin(TechnicalDocument, admin.site)
        form = SimpleNamespace(cleaned_data={"status_note": "İncelemeye gönderildi."})

        model_admin.save_model(self.request, document, form, change=True)

        history = TechnicalDocumentStatusHistory.objects.get(document=document)
        self.assertEqual(history.from_status, TechnicalDocument.STATUS_DRAFT)
        self.assertEqual(history.to_status, TechnicalDocument.STATUS_IN_REVIEW)
        self.assertEqual(history.note, "İncelemeye gönderildi.")
        self.assertEqual(history.changed_by, self.admin_user)

        change_url = reverse("admin:api_technicaldocument_change", args=(document.pk,))
        self.assertEqual(self.client.get(change_url).status_code, 200)

    def test_technical_document_admin_does_not_record_unchanged_status(self):
        project = Project.objects.create(name="Test Projesi", code="TP")
        document = TechnicalDocument.objects.create(
            project=project,
            code="TD-002",
            title="Değişmeyen Doküman",
            status=TechnicalDocument.STATUS_DRAFT,
            created_by=self.admin_user,
            updated_by=self.admin_user,
        )
        model_admin = TechnicalDocumentAdmin(TechnicalDocument, admin.site)
        form = SimpleNamespace(cleaned_data={"status_note": ""})

        model_admin.save_model(self.request, document, form, change=True)

        self.assertFalse(TechnicalDocumentStatusHistory.objects.filter(document=document).exists())

    def test_technical_document_admin_rejects_cross_project_relations(self):
        project = Project.objects.create(name="Ana Proje", code="ANA")
        other_project = Project.objects.create(name="Diğer Proje", code="DIG")
        other_cover_page = CoverPage.objects.create(
            project=other_project,
            number="CP-1",
            issue="A",
        )
        other_panel = ProjectPanel.objects.create(project=other_project, name="Yapısal")
        form = TechnicalDocumentAdminForm(
            data={
                "project": project.pk,
                "cover_page": other_cover_page.pk,
                "panels": [other_panel.pk],
                "code": "TD-003",
                "title": "İlişki Testi",
                "revision": "A",
                "status": TechnicalDocument.STATUS_DRAFT,
                "priority": TechnicalDocument.PRIORITY_NORMAL,
                "classification": TechnicalDocument.CLASSIFICATION_INTERNAL,
                "last_notification_recipient_count": 0,
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("cover_page", form.errors)
        self.assertIn("panels", form.errors)
