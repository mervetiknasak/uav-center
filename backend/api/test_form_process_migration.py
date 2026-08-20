from datetime import date

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class FlightPermitToFormMigrationTests(TransactionTestCase):
    migrate_from = ("api", "0021_formprocessrecord")
    migrate_to = ("api", "0023_remove_flightpermit")

    def setUp(self):
        super().setUp()
        executor = MigrationExecutor(connection)
        executor.migrate([self.migrate_from])
        old_apps = executor.loader.project_state([self.migrate_from]).apps
        FlightPermit = old_apps.get_model("api", "FlightPermit")
        FlightPermit.objects.create(
            permit_applicant="TUSAŞ",
            permit_number="UI-2026-7",
            template_code="institution_c",
            template_data={
                "coordination_contact": "Operasyon Birimi",
                "coordination_reference": "KR-7",
                "operational_notes": "Test sahası koordinasyonu",
            },
            aircraft_nationality="TR",
            aircraft_id_mark="TC-UAV-7",
            aircraft_owner="UAV Center",
            aircraft_type="Test Platformu",
            aircraft_manufacturer="UAV Center",
            serial_number="SN-7",
            purpose_of_flight=["option_1", "option_6"],
            target_date=date(2026, 9, 1),
            flight_duration=3,
            aircraft_configuration="Test konfigürasyonu",
            conditions_restrictions="Test sahası",
            conditions_substantiations="Koşul raporu",
            valid_from=date(2026, 8, 20),
            valid_until=date(2026, 10, 20),
            status="approved",
            notes="Taşınacak not",
            document="flight_permits/2026/08/izin.pdf",
            document_name="izin.pdf",
            document_content_type="application/pdf",
            document_size=2048,
        )

        executor = MigrationExecutor(connection)
        executor.migrate([self.migrate_to])
        self.apps = executor.loader.project_state([self.migrate_to]).apps

    def test_migrates_record_fields_status_and_attachment_without_legacy_model(self):
        FormProcessRecord = self.apps.get_model("api", "FormProcessRecord")
        record = FormProcessRecord.objects.get()

        self.assertEqual(record.process_code, "flight-permits")
        self.assertEqual(record.template_code, "fm_qua_0581")
        self.assertEqual(record.record_number, "UI-2026-7")
        self.assertEqual(record.status, "approved")
        self.assertEqual(record.data["purpose_of_flight"], ["option_1", "option_6"])
        self.assertEqual(record.data["coordination_reference"], "KR-7")
        self.assertEqual(record.attachment.name, "flight_permits/2026/08/izin.pdf")
        self.assertEqual(record.attachment_name, "izin.pdf")
        with self.assertRaises(LookupError):
            self.apps.get_model("api", "FlightPermit")
