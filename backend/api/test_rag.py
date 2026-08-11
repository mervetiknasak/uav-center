from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import AnalysisControl, Document
from .services.rag_service import index_document, retrieve, split_text


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
        self.assertEqual(first_hashes, list(self.document.chunks.values_list("content_hash", flat=True)))
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


class RagApiTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="rag-user", password="StrongPass123!")
        self.other_user = user_model.objects.create_user(username="other", password="StrongPass123!")
        self.client.force_login(self.user)
        self.document = Document.objects.create(
            original_name="uçuş.txt",
            file="documents/ucus.txt",
            extracted_text="REQ-FLT-001 İrtifa bilgisi doğrulanmalıdır. TODO Limit belirlenecek.",
            status=Document.STATUS_PROCESSED,
        )
        index_document(self.document)

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
