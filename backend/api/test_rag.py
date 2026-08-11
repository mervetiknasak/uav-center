from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import AnalysisControl, Document, DocumentAnalysisRun
from .services.ai_wrapper import AIProviderError
from .services.rag_service import answer_document_query, index_document, retrieve, split_text


class RagServiceTests(TestCase):
    def setUp(self):
        self.document = Document.objects.create(
            original_name="gereksinimler.txt",
            file="documents/gereksinimler.txt",
            extracted_text=(
                "REQ-FLT-001 Uçuş kontrol sistemi irtifayı saniyede on kez ölçmelidir.\n\n"
                "REQ-PWR-002 Güç sistemi 28 volt besleme kullanmalıdır. Kabul kriteri gerilim "
                "toleransının yüzde iki içinde olmasıdır.\n\n"
                "TODO Motor sıcaklığı üst sınırı daha sonra belirlenecek."
            ),
            status=Document.STATUS_PROCESSED,
        )

    @override_settings(RAG_CHUNK_SIZE=200, RAG_CHUNK_OVERLAP=40)
    def test_index_is_repeatable_and_keeps_citable_offsets(self):
        first_count = index_document(self.document)
        first_hashes = list(self.document.chunks.values_list("content_hash", flat=True))
        second_count = index_document(self.document)

        self.assertEqual(first_count, second_count)
        self.assertEqual(
            first_hashes, list(self.document.chunks.values_list("content_hash", flat=True))
        )
        for chunk in self.document.chunks.all():
            self.assertEqual(
                self.document.extracted_text[chunk.char_start : chunk.char_end],
                chunk.content,
            )

    def test_retrieval_ranks_relevant_evidence_and_returns_source_id(self):
        index_document(self.document)

        sources = retrieve(self.document, "28 volt güç sistemi", top_k=2)

        self.assertEqual(sources[0]["id"], f"D{self.document.id}-C1")
        self.assertIn("28 volt", sources[0]["text"])

    def test_split_text_rejects_invalid_overlap(self):
        with self.assertRaises(ValueError):
            split_text("örnek", max_chars=200, overlap=200)

    def test_provider_fallback_exposes_only_stable_public_error(self):
        class FailingAI:
            def generate(self, *_args, **_kwargs):
                raise AIProviderError("token=secret http://10.0.0.8:11434/api /private/model.bin")

        index_document(self.document)
        result = answer_document_query(self.document, "güç sistemi", ai=FailingAI())

        self.assertEqual(result["provider_error"], "AI sağlayıcısı kullanılamadı.")
        self.assertNotIn("10.0.0.8", result["provider_error"])


class RagApiTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="rag-user", password="StrongPass123!")
        self.other_user = user_model.objects.create_user(
            username="other", password="StrongPass123!"
        )
        self.client.force_login(self.user)
        self.document = Document.objects.create(
            original_name="uçuş.txt",
            file="documents/ucus.txt",
            owner=self.user,
            extracted_text="REQ-FLT-001 İrtifa bilgisi doğrulanmalıdır. TODO Limit belirlenecek.",
            status=Document.STATUS_PROCESSED,
        )
        index_document(self.document)

    def test_document_endpoints_are_isolated_by_owner(self):
        foreign_document = Document.objects.create(
            original_name="gizli.txt",
            file="documents/gizli.txt",
            owner=self.other_user,
            extracted_text="Gizli gereksinim",
            status=Document.STATUS_PROCESSED,
        )
        unowned_document = Document.objects.create(
            original_name="legacy.txt",
            file="documents/legacy.txt",
            extracted_text="Sahibi belirlenemeyen eski belge",
            status=Document.STATUS_PROCESSED,
        )

        listed_ids = {item["id"] for item in self.client.get(reverse("document-list")).json()}
        self.assertEqual(listed_ids, {self.document.id})
        for document in (foreign_document, unowned_document):
            kwargs = {"document_id": document.id}
            self.assertEqual(
                self.client.get(reverse("document-detail", kwargs=kwargs)).status_code, 404
            )
            self.assertEqual(
                self.client.post(
                    reverse("document-rag-query", kwargs=kwargs),
                    data={"query": "Gereksinim nedir?"},
                    content_type="application/json",
                ).status_code,
                404,
            )
            self.assertEqual(
                self.client.post(
                    reverse("document-control-run", kwargs=kwargs),
                    data={"control_ids": []},
                    content_type="application/json",
                ).status_code,
                404,
            )
            self.assertEqual(
                self.client.get(reverse("document-analysis-runs", kwargs=kwargs)).status_code,
                404,
            )
            self.assertEqual(
                self.client.delete(reverse("document-detail", kwargs=kwargs)).status_code, 404
            )
            self.assertTrue(Document.objects.filter(pk=document.pk).exists())

    def test_staff_can_access_owned_and_unowned_documents(self):
        staff = get_user_model().objects.create_user(
            username="document-admin",
            password="StrongPass123!",
            is_staff=True,
        )
        legacy_document = Document.objects.create(
            original_name="legacy.txt",
            file="documents/legacy.txt",
            extracted_text="Eski belge",
            status=Document.STATUS_PROCESSED,
        )
        run = DocumentAnalysisRun.objects.create(
            document=self.document,
            created_by=self.user,
            status=DocumentAnalysisRun.STATUS_COMPLETED,
        )
        self.client.force_login(staff)

        listed_documents = self.client.get(reverse("document-list")).json()
        listed_ids = {item["id"] for item in listed_documents}
        self.assertEqual(listed_ids, {self.document.id, legacy_document.id})
        listed_by_id = {item["id"]: item for item in listed_documents}
        self.assertEqual(listed_by_id[self.document.id]["owner_id"], self.user.id)
        self.assertEqual(listed_by_id[self.document.id]["owner_name"], self.user.username)
        self.assertIsNone(listed_by_id[legacy_document.id]["owner_id"])
        self.assertIsNone(listed_by_id[legacy_document.id]["owner_name"])
        self.assertEqual(
            self.client.get(
                reverse("document-detail", kwargs={"document_id": legacy_document.id})
            ).status_code,
            200,
        )
        history_response = self.client.get(
            reverse(
                "document-analysis-runs",
                kwargs={"document_id": self.document.id},
            )
        )
        self.assertEqual(history_response.status_code, 200)
        self.assertEqual([item["id"] for item in history_response.json()], [run.id])

    def test_user_can_create_update_and_delete_own_control(self):
        created = self.client.post(
            reverse("analysis-control-list"),
            data={
                "name": "Birim kontrolü",
                "description": "SI birimlerini inceler",
                "instructions": "Her sayısal büyüklüğün yanında bir SI birimi bulunduğunu kontrol et.",
                "severity": "warning",
            },
            content_type="application/json",
        )
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.json()["kind"], "custom")

        control_id = created.json()["database_id"]
        updated = self.client.patch(
            reverse("analysis-control-detail", kwargs={"control_id": control_id}),
            data={"severity": "critical"},
            content_type="application/json",
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["severity"], "critical")

        self.client.delete(reverse("analysis-control-detail", kwargs={"control_id": control_id}))
        self.assertFalse(AnalysisControl.objects.filter(pk=control_id).exists())

    def test_controls_are_isolated_per_user(self):
        foreign_control = AnalysisControl.objects.create(
            owner=self.other_user,
            name="Gizli kontrol",
            instructions="Bu kontrol yalnızca diğer kullanıcıya görünmelidir.",
        )

        response = self.client.get(reverse("analysis-control-list"))

        ids = {item["id"] for item in response.json()}
        self.assertNotIn(f"custom:{foreign_control.id}", ids)

    @patch("api.services.rag_service.AIWrapper.generate")
    def test_rag_query_returns_grounded_sources_and_persists_run(self, generate):
        generate.return_value = {
            "provider": "ollama",
            "model": "gemma4:e4b",
            "response": "İrtifa bilgisi doğrulanmalıdır. [D1-C1]",
        }

        response = self.client.post(
            reverse("document-rag-query", kwargs={"document_id": self.document.id}),
            data={"query": "İrtifa nasıl doğrulanıyor?", "top_k": 3},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["result"]["grounded"])
        self.assertEqual(response.json()["result"]["sources"][0]["document_id"], self.document.id)
        self.assertEqual(self.document.analysis_runs.count(), 1)

    @patch("api.documents.views.answer_document_query")
    def test_failed_run_persists_only_redacted_bounded_error(self, query):
        query.side_effect = RuntimeError(
            "token=secret http://10.0.0.8:11434/api /Users/operator/model.bin pilot@example.com"
        )

        response = self.client.post(
            reverse("document-rag-query", kwargs={"document_id": self.document.id}),
            data={"query": "İrtifa nasıl doğrulanıyor?"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["detail"], "Doküman sorgusu tamamlanamadı.")
        run = DocumentAnalysisRun.objects.get(pk=response.json()["run_id"])
        self.assertNotIn("secret", run.error_message)
        self.assertNotIn("10.0.0.8", run.error_message)
        self.assertNotIn("/Users/operator", run.error_message)
        self.assertNotIn("pilot@example.com", run.error_message)

    @patch("api.documents.views.run_document_controls")
    def test_invalid_control_request_does_not_echo_internal_detail(self, controls):
        controls.side_effect = ValueError("invalid /private/rules.json admin@example.com")

        response = self.client.post(
            reverse("document-control-run", kwargs={"document_id": self.document.id}),
            data={"control_ids": ["custom:999"]},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Doküman kontrol isteği geçersiz.")
        self.assertNotIn("/private", response.content.decode())
        run = DocumentAnalysisRun.objects.get(pk=response.json()["run_id"])
        self.assertNotIn("/private", run.error_message)
        self.assertNotIn("admin@example.com", run.error_message)

    def test_system_controls_detect_unresolved_marker(self):
        response = self.client.post(
            reverse("document-control-run", kwargs={"document_id": self.document.id}),
            data={"control_ids": ["unresolved-markers"]},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        result = response.json()["result"]["controls"][0]
        self.assertEqual(result["outcome"], "failed")
        self.assertTrue(result["sources"])
