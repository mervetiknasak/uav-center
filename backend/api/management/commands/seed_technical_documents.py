from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from api.models import Project, TechnicalDocument, TechnicalDocumentStatusHistory


class Command(BaseCommand):
    help = "Mevcut projeler için idempotent teknik doküman demo kayıtları oluşturur."

    def handle(self, *args, **options):
        projects = list(Project.objects.prefetch_related("panels").all())
        if not projects:
            self.stdout.write(self.style.WARNING("Proje bulunamadı; demo dokümanı oluşturulmadı."))
            return

        today = timezone.localdate()
        templates = [
            {
                "suffix": "SYS-001",
                "title": "Sistem Gereksinimleri Dokümanı",
                "description": "Sistem seviyesi fonksiyonel ve performans gereksinimleri.",
                "category": "Sistem Mühendisliği",
                "document_type": "Gereksinim",
                "revision": "B",
                "status": TechnicalDocument.STATUS_PUBLISHED,
                "priority": TechnicalDocument.PRIORITY_CRITICAL,
                "publication_date": today - timedelta(days=18),
                "due_date": today - timedelta(days=18),
                "review_date": today + timedelta(days=162),
                "owner_name": "Sistem Mühendisliği",
            },
            {
                "suffix": "DES-014",
                "title": "Ön Tasarım Gözden Geçirme Paketi",
                "description": "Alt sistem tasarım kararları, arayüzler ve açık aksiyonlar.",
                "category": "Tasarım",
                "document_type": "Tasarım Tanımı",
                "revision": "A.3",
                "status": TechnicalDocument.STATUS_IN_REVIEW,
                "priority": TechnicalDocument.PRIORITY_HIGH,
                "due_date": today + timedelta(days=6),
                "owner_name": "Tasarım Ofisi",
            },
            {
                "suffix": "TST-008",
                "title": "Çevresel Test Prosedürü",
                "description": "Titreşim, sıcaklık ve nem testlerinin kabul kriterleri.",
                "category": "Doğrulama",
                "document_type": "Test Prosedürü",
                "revision": "A",
                "status": TechnicalDocument.STATUS_CHANGES_REQUESTED,
                "priority": TechnicalDocument.PRIORITY_NORMAL,
                "due_date": today - timedelta(days=3),
                "owner_name": "Test ve Doğrulama",
            },
            {
                "suffix": "ICD-003",
                "title": "Aviyonik Veri Arayüzü Kontrol Dokümanı",
                "description": "Veri yolu mesajları, sinyal tanımları ve zamanlama bütçeleri.",
                "category": "Arayüz",
                "document_type": "ICD",
                "revision": "C",
                "status": TechnicalDocument.STATUS_APPROVED,
                "priority": TechnicalDocument.PRIORITY_HIGH,
                "due_date": today + timedelta(days=2),
                "owner_name": "Aviyonik Ekibi",
            },
        ]

        created_count = 0
        for project in projects:
            panel_ids = list(project.panels.values_list("id", flat=True))
            for index, template in enumerate(templates):
                code = f"{project.code.upper()}-{template['suffix']}"
                values = {key: value for key, value in template.items() if key != "suffix"}
                document, created = TechnicalDocument.objects.update_or_create(
                    project=project,
                    code=code,
                    defaults=values,
                )
                if panel_ids:
                    if index == 0 and len(panel_ids) > 1:
                        document.panels.set(panel_ids)
                    else:
                        document.panels.set([panel_ids[index % len(panel_ids)]])
                if created:
                    TechnicalDocumentStatusHistory.objects.create(
                        document=document,
                        to_status=document.status,
                        note="Demo doküman kaydı oluşturuldu.",
                    )
                    created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"{created_count} yeni demo dokümanı oluşturuldu; mevcut kayıtlar güncellendi."
            )
        )
