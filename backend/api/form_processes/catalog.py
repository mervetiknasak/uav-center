"""Versioned FM form catalog and template-owned field validation."""

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

TEMPLATE_DIRECTORY = Path(__file__).resolve().parent / "templates"


@dataclass(frozen=True)
class FormField:
    key: str
    label: str
    field_type: str = "text"
    group: str = "Genel Bilgiler"
    required: bool = False
    max_length: int = 500
    placeholder: str = ""
    options: tuple[tuple[str, str], ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "label": self.label,
            "type": self.field_type,
            "group": self.group,
            "required": self.required,
            "max_length": self.max_length,
            "placeholder": self.placeholder,
            "options": [{"value": value, "label": label} for value, label in self.options],
        }


@dataclass(frozen=True)
class FormTemplate:
    code: str
    process_code: str
    process_name: str
    form_number: str
    title: str
    description: str
    fields: tuple[FormField, ...]

    @property
    def document_path(self) -> Path:
        return TEMPLATE_DIRECTORY / f"{self.code}.docx"

    def as_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "process_code": self.process_code,
            "process_name": self.process_name,
            "form_number": self.form_number,
            "title": self.title,
            "description": self.description,
            "fields": [field.as_dict() for field in self.fields],
        }


def text(
    key: str,
    label: str,
    *,
    group: str = "Genel Bilgiler",
    required: bool = False,
    max_length: int = 500,
    placeholder: str = "",
) -> FormField:
    return FormField(key, label, "text", group, required, max_length, placeholder)


def area(
    key: str,
    label: str,
    *,
    group: str,
    required: bool = False,
    max_length: int = 20_000,
) -> FormField:
    return FormField(key, label, "textarea", group, required, max_length)


def day(key: str, label: str, *, group: str = "Tarih ve Onay") -> FormField:
    return FormField(key, label, "date", group, False, 10)


def choice(
    key: str,
    label: str,
    options: tuple[tuple[str, str], ...],
    *,
    group: str = "Genel Bilgiler",
) -> FormField:
    return FormField(key, label, "select", group, False, 120, options=options)


APPROVAL_FIELDS = (
    text("prepared_by", "Hazırlayan", group="Tarih ve Onay"),
    text("approved_by", "Onaylayan", group="Tarih ve Onay"),
    text("authorized_by", "Yetkilendiren", group="Tarih ve Onay"),
    day("approval_date", "Onay tarihi"),
)

AWSS_IDENTITY_FIELDS = (
    text("program", "Program / Proje", required=True),
    text("ata_index", "ATA indeks"),
    text("ata_chapter", "ATA bölüm"),
    text("aircraft_type", "Hava aracı tipi", required=True),
    text("aircraft_serial_number", "Hava aracı seri numarası"),
    area("purpose", "Amaç", group="Doküman Kapsamı"),
    area("scope", "Kapsam", group="Doküman Kapsamı"),
    area("applicability", "Uygulanabilirlik", group="Doküman Kapsamı"),
    area("compliance_statement", "Uyum beyanı", group="Sonuç ve Kaynaklar"),
    area("proposed_limitations", "Önerilen sınırlamalar", group="Sonuç ve Kaynaklar"),
    area("flight_clearance_statement", "Uçuş izni beyanı", group="Sonuç ve Kaynaklar"),
    area("references", "Referanslar", group="Sonuç ve Kaynaklar"),
    area("related_procedures", "İlgili prosedürler", group="Sonuç ve Kaynaklar"),
    area("attachments", "Ekler", group="Sonuç ve Kaynaklar"),
)


def awss_fields(*discipline_fields: tuple[str, str]) -> tuple[FormField, ...]:
    return (
        *AWSS_IDENTITY_FIELDS,
        *(area(key, label, group="Teknik Değerlendirme") for key, label in discipline_fields),
        *APPROVAL_FIELDS,
    )


MISSION_FIELDS = (
    text("mission_letter_number", "Görevlendirme yazısı numarası", required=True),
    day("issue_date", "Yayın tarihi"),
    text("person_name", "Ad ve soyad", required=True),
    day("date_of_birth", "Doğum tarihi", group="Personel Bilgileri"),
    text("company_department", "Şirket ve bölüm", group="Personel Bilgileri"),
    text("title", "Unvan", group="Personel Bilgileri"),
    text("paf_number", "PAF numarası", group="Personel Bilgileri"),
    area("assigned_projects", "Atanan projeler", group="Görevlendirme"),
    area("discipline_scope", "Disiplin ve kapsam", group="Görevlendirme"),
    area("reporting_lines", "Raporlama hatları", group="Görevlendirme"),
    area("accountabilities", "Sorumluluklar", group="Görevlendirme"),
    text("employee_signature", "Personel imzası", group="Tarih ve Onay"),
    day("employee_signature_date", "Personel imza tarihi"),
    text("authorized_by", "Yetkilendiren", group="Tarih ve Onay"),
    day("authorization_date", "Yetkilendirme tarihi"),
    area("cancellation_reason", "İptal nedeni", group="İptal"),
)

AUTHORIZATION_FIELDS = (
    text("authorization_id", "Yetkilendirme kimliği", required=True),
    text("employee_number", "Personel numarası"),
    text("person_name", "Ad ve soyad", required=True),
    text("employee_id", "Personel kimliği"),
    day("date_of_birth", "Doğum tarihi", group="Personel Bilgileri"),
    text("authorization_period", "Yetkilendirme dönemi", group="Yetkilendirme"),
    choice(
        "competencies_met",
        "Asgari yeterlilikler karşılandı mı?",
        (("yes", "Evet"), ("no", "Hayır")),
        group="Yetkilendirme",
    ),
    area("competency_notes", "Yeterlilik değerlendirmesi", group="Yetkilendirme"),
    text("evaluator_name", "Değerlendiren", group="Tarih ve Onay"),
    day("evaluation_date", "Değerlendirme tarihi"),
    text("authorized_position", "Yetkilendirilen görev", group="Yetkilendirme"),
    text("authorizer_name", "Yetkilendiren", group="Tarih ve Onay"),
    day("authorization_date", "Yetkilendirme tarihi"),
)

PTF_IDENTITY_FIELDS = (
    text("applicant", "Başvuru sahibi", required=True),
    text("application_number", "Başvuru / form numarası"),
    text("aircraft_owner", "Hava aracı sahibi"),
    text("aircraft_model", "Hava aracı modeli / tipi"),
    text("serial_number", "Seri numarası"),
    area("aircraft_configuration", "Hava aracı konfigürasyonu", group="Uçuş Bilgileri"),
    area("purpose_scope", "Uçuş amacı / kapsamı", group="Uçuş Bilgileri"),
    area("conditions_restrictions", "Koşullar ve kısıtlamalar", group="Uçuş Bilgileri"),
    area("substantiations", "Kanıtlar / dayanaklar", group="Uçuş Bilgileri"),
    day("issue_date", "Yayın tarihi"),
    text("signer_name", "İsim ve imza", group="Tarih ve Onay"),
)


FORM_TEMPLATES = (
    FormTemplate(
        "fm_dsg_0328",
        "awss-kapak",
        "AWSS Kapak",
        "FM.DSG.0328",
        "Yapısal Uçuşa Elverişlilik Durum Değerlendirmesi",
        "Yapısal analiz, test ve konfigürasyon durum özeti.",
        awss_fields(
            ("load_data_basis", "Yük veri tabanı / yük veri temeli"),
            ("structural_configuration", "Yapısal konfigürasyon"),
            ("static_test_results", "Statik test sonuçları"),
            ("fatigue_test_results", "Yorulma test sonuçları"),
            ("design_areas", "Tasarım alanları"),
            ("modifications", "Modifikasyonlar"),
            ("concessions", "İmtiyazlar"),
            ("stress_fatigue_damage_tolerance", "Gerilme, yorulma ve hasar toleransı"),
            ("material_qualification", "Malzeme kalifikasyonu"),
            ("particular_risk_analysis", "Özel risk analizi"),
            ("certification_status", "Sertifikasyon gereksinimleri uyum durumu"),
        ),
    ),
    FormTemplate(
        "fm_dsg_0329",
        "awss-kapak",
        "AWSS Kapak",
        "FM.DSG.0329",
        "Yükler ve Aeroelastisite Uçuşa Elverişlilik Durum Değerlendirmesi",
        "Yükler, uçuş zarfı ve aeroelastisite durum özeti.",
        awss_fields(
            ("load_data_basis", "Yük veri tabanı / yük veri temeli"),
            ("aircraft_geometry", "Hava aracı tanımı ve geometrik veriler"),
            ("configuration", "Konfigürasyon"),
            ("mass_data", "Kütle verisi ve çalışma koşulları"),
            ("flight_envelope", "Tasarım hızları ve uçuş zarfı"),
            ("aerodynamic_data", "Aerodinamik veri"),
            ("structural_data", "Yapısal veri"),
            ("landing_gear_data", "İniş takımları verisi"),
            ("flight_control_data", "Uçuş kontrol sistemi verisi"),
            ("aircraft_design_loads", "Hava aracı tasarım yükleri"),
            ("aeroelasticity_data", "Aeroelastisite modeli ve veri tabanı"),
            ("operational_limitations", "Operasyonel sınırlamalar"),
            ("flight_test_monitoring", "Uçuş test izleme"),
            ("certification_status", "Sertifikasyon gereksinimleri uyum durumu"),
        ),
    ),
    FormTemplate(
        "fm_dsg_0330",
        "awss-kapak",
        "AWSS Kapak",
        "FM.DSG.0330",
        "Güç Ünitesi Montajı Uçuşa Elverişlilik Durum Değerlendirmesi",
        "Güç ünitesi montajı ve kalifikasyon durum özeti.",
        awss_fields(
            ("aircraft_definition", "Hava aracı / güç ünitesi tanımı"),
            ("available_functions", "Mevcut fonksiyonlar"),
            ("configuration_summary", "Konfigürasyon özeti"),
            ("thrust_system_models", "İtki sistemi modelleri ve veri tabanı"),
            ("equipment_dal_list", "Ekipman DAL listesi"),
            ("software_status", "Yazılım kalifikasyon durumu"),
            ("hardware_status", "Donanım kalifikasyon durumu"),
            ("environmental_qualification", "Çevresel kalifikasyon"),
            ("hazardous_failure_conditions", "Potansiyel tehlikeli hata koşulları"),
            ("engine_status", "Motor / pervane tip sertifikası durumu"),
            ("operating_limitations", "Operasyonel sınırlamalar"),
            ("test_analysis_status", "Sistem testleri ve analiz durumu"),
            ("particular_risk_analysis", "Özel risk analizi"),
            ("certification_status", "Sertifikasyon gereksinimleri uyum durumu"),
        ),
    ),
    FormTemplate(
        "fm_dsg_0331",
        "awss-kapak",
        "AWSS Kapak",
        "FM.DSG.0331",
        "Hava Aracı Performansı ve Kumanda Edilebilirlik Durum Değerlendirmesi",
        "Performans ve kumanda edilebilirlik durum özeti.",
        awss_fields(
            ("models_database", "Performans, stabilite ve kontrol modelleri / veri tabanı"),
            ("flight_envelope", "Uçuş zarfı"),
            ("performance_analysis", "Performans analiz sonuçları"),
            ("failure_cases", "Hata durumları değerlendirmesi"),
            ("weight_balance", "Ağırlık ve denge"),
            ("emergency_procedures", "Taslak acil durum prosedürleri"),
            ("certification_status", "Sertifikasyon gereksinimleri uyum durumu"),
        ),
    ),
    FormTemplate(
        "fm_dsg_0332",
        "awss-kapak",
        "AWSS Kapak",
        "FM.DSG.0332",
        "Sistemler Uçuşa Elverişlilik Durum Değerlendirmesi",
        "Sistem emniyeti, kalifikasyon ve uyum durum özeti.",
        awss_fields(
            ("aircraft_definition", "Hava aracı / sistem tanımı"),
            ("available_functions", "Mevcut fonksiyonlar"),
            ("equipment_dal_list", "Ekipman DAL listesi"),
            ("software_status", "Yazılım kalifikasyon durumu"),
            ("hardware_status", "Donanım kalifikasyon durumu"),
            ("environmental_qualification", "Çevresel kalifikasyon"),
            ("catastrophic_failure_conditions", "Felaketle sonuçlanabilecek hata koşulları"),
            ("particular_risk_analysis", "Özel risk analizi"),
            ("certification_status", "Sertifikasyon gereksinimleri uyum durumu"),
            ("incomplete_tests", "Tamamlanmamış test ve analizler"),
        ),
    ),
    FormTemplate(
        "fm_dsg_0344",
        "awss-kapak",
        "AWSS Kapak",
        "FM.DSG.0344",
        "İnsan Faktörleri Uçuşa Elverişlilik Durum Değerlendirmesi",
        "İnsan faktörleri analiz ve doğrulama durum özeti.",
        awss_fields(
            ("validation_models_database", "İnsan faktörleri modelleri ve veri tabanı"),
            ("cockpit_cabin_design", "Kokpit / kabin iç tasarımı"),
            ("analysis_results", "İnsan faktörleri analiz sonuçları"),
            ("certification_status", "Sertifikasyon gereksinimleri uyum durumu"),
        ),
    ),
    FormTemplate(
        "fm_dsg_0625",
        "awss-kapak",
        "AWSS Kapak",
        "FM.DSG.0625",
        "Yazılım Uçuşa Elverişlilik Durum Değerlendirmesi",
        "Yazılım DAL, kalifikasyon ve emniyet durum özeti.",
        awss_fields(
            ("available_functions", "Mevcut fonksiyonlar"),
            ("equipment_list", "Yazılım içeren ekipman listesi"),
            ("software_status", "Yazılım kalifikasyon durumu"),
            ("hardware_status", "Donanım kalifikasyon durumu"),
            ("environmental_qualification", "Çevresel kalifikasyon"),
            ("hazardous_failure_conditions", "Tehlikeli hata koşulları"),
            ("particular_risk_analysis", "Özel risk analizi"),
            ("certification_status", "Sertifikasyon gereksinimleri uyum durumu"),
            ("incomplete_tests", "Tamamlanmamış test ve analizler"),
        ),
    ),
    FormTemplate(
        "fm_dsg_0626",
        "awss-kapak",
        "AWSS Kapak",
        "FM.DSG.0626",
        "Donanım Uçuşa Elverişlilik Durum Değerlendirmesi",
        "Donanım DAL, kalifikasyon ve emniyet durum özeti.",
        awss_fields(
            ("available_functions", "Mevcut fonksiyonlar"),
            ("equipment_list", "Donanım içeren ekipman listesi"),
            ("hardware_status", "Donanım kalifikasyon durumu"),
            ("software_status", "Yazılım kalifikasyon durumu"),
            ("environmental_qualification", "Çevresel kalifikasyon"),
            ("hazardous_failure_conditions", "Tehlikeli hata koşulları"),
            ("particular_risk_analysis", "Özel risk analizi"),
            ("certification_status", "Sertifikasyon gereksinimleri uyum durumu"),
            ("incomplete_tests", "Tamamlanmamış test ve analizler"),
        ),
    ),
    FormTemplate(
        "fm_dsg_0063e",
        "cdi",
        "CDI",
        "FM.DSG.0063E",
        "Compliance Demonstration Item (CDI) Cover Page",
        "CDI sınıflandırma, LoI ve uyum gösterim kapak formu.",
        (
            text("program", "Program", required=True),
            text("ata_index", "ATA indeks"),
            text("ata_subject", "ATA konu"),
            text("aircraft_type", "Hava aracı tipi"),
            text("cdi_name", "CDI adı", required=True),
            text("primary_panel", "Birincil panel"),
            text("secondary_panel", "İkincil panel"),
            area("affected_requirements", "Etkilenen gereksinimler", group="Değerlendirme"),
            area("subject", "Konu", group="Değerlendirme"),
            area("novelty", "Yenilik", group="Değerlendirme"),
            area("complexity", "Karmaşıklık", group="Değerlendirme"),
            area("doa_panel_performance", "DOA panel performansı", group="Değerlendirme"),
            area("criticality", "Kritiklik", group="Değerlendirme"),
            text("risk_class", "Risk sınıfı", group="Değerlendirme"),
            area("loi_proposal", "LoI önerisi", group="Değerlendirme"),
            area("submitted_documents", "Sunulan dokümanlar", group="Kaynaklar"),
            area("compliance_statement", "Uyum beyanı", group="Kaynaklar"),
            *APPROVAL_FIELDS,
        ),
    ),
    FormTemplate(
        "fm_dsg_0307e",
        "change-process",
        "Change Process",
        "FM.DSG.0307E",
        "Type Design Change Classification Table",
        "Tip tasarım değişikliği sınıflandırma tablosu.",
        (
            text("project", "Proje", required=True),
            text("change_title", "Değişiklik başlığı", required=True),
            text("change_reference", "Değişiklik referansı"),
            area("applicability", "Uygulanabilirlik", group="Sınıflandırma"),
            area("affected_documents", "Etkilenen dokümanlar", group="Sınıflandırma"),
            area("compliance_documents", "Uyum dokümanları", group="Sınıflandırma"),
            area(
                "environmental_requirements",
                "Çevresel koruma gereksinimleri",
                group="Sınıflandırma",
            ),
            area(
                "operational_suitability_data", "Operasyonel uygunluk verisi", group="Sınıflandırma"
            ),
            area("design_change_assessment", "Tasarım değişikliği değerlendirmesi", group="Karar"),
            choice(
                "classification",
                "Sınıflandırma",
                (("minor", "Minor"), ("major", "Major")),
                group="Karar",
            ),
            text("classification_controlled_by", "Sınıflandırmayı kontrol eden", group="Karar"),
            text("approval_reference", "Onay referansı", group="Karar"),
        ),
    ),
    FormTemplate(
        "fm_dsg_0308e",
        "change-process",
        "Change Process",
        "FM.DSG.0308E",
        "Significant / Not Significant Decision Table for a Major Change",
        "Major değişiklik için significant / not significant karar formu.",
        (
            text("design_change_number", "Tasarım değişikliği numarası", required=True),
            text("project", "Proje", required=True),
            area("applicability", "Uygulanabilirlik", group="Değişiklik"),
            text("change_title", "Değişiklik başlığı", group="Değişiklik"),
            text("classification_reference", "Sınıflandırma referansı", group="Değişiklik"),
            area("classification_answers", "Sınıflandırma soruları ve cevapları", group="Karar"),
            choice(
                "decision",
                "Karar",
                (("significant", "Significant"), ("not_significant", "Not Significant")),
                group="Karar",
            ),
            area("conclusion", "Sonuç", group="Karar"),
            text("signer_name", "İmzalayan", group="Tarih ve Onay"),
            day("signature_date", "İmza tarihi"),
        ),
    ),
    FormTemplate(
        "fm_dsg_0309e",
        "change-process",
        "Change Process",
        "FM.DSG.0309E",
        "Design Change Approval Sheet for Certification",
        "Sertifikasyon amaçlı tasarım değişikliği onay formu.",
        (
            text("design_change_number", "Tasarım değişikliği numarası", required=True),
            text("form_number", "Form numarası"),
            text("project", "Proje", required=True),
            text("issue_number", "Yayın numarası"),
            day("issue_date", "Yayın tarihi"),
            area("description", "Değişiklik açıklaması", group="Değişiklik"),
            area("reason", "Değişiklik nedeni", group="Değişiklik"),
            area("applicability", "Hava aracı uygulanabilirliği", group="Değişiklik"),
            area("general_description", "Genel açıklama", group="Değişiklik"),
            area("affected_requirements", "Etkilenen sertifikasyon gereksinimleri", group="Uyum"),
            area("impacts_on_documents", "Onaylı dokümanlara etkiler", group="Uyum"),
            choice(
                "approval_type", "Onay tipi", (("minor", "Minor"), ("major", "Major")), group="Onay"
            ),
            text("approver_name", "Onaylayan", group="Onay"),
            day("approval_date", "Onay tarihi"),
        ),
    ),
    FormTemplate(
        "fm_dsg_0464e",
        "cover-page",
        "Cover Page",
        "FM.DSG.0464E",
        "Compliance Document Cover Page",
        "Uyum dokümanı kapak sayfası.",
        (
            text("compliance_document_number", "Uyum dokümanı numarası", required=True),
            text("issue_number", "Yayın numarası"),
            text("program_project", "Program / Proje", required=True),
            text("ata_index", "ATA indeks"),
            text("ata_chapter", "ATA bölüm"),
            text("aircraft_type", "Hava aracı tipi"),
            text("document_subject", "Doküman konusu"),
            area("requirement_reference", "Gereksinim referansı", group="Uyum"),
            text("authority_level_of_involvement", "Otorite katılım seviyesi", group="Uyum"),
            text("cdi_number", "CDI numarası", group="Uyum"),
            area("compliance_means", "Uyum yöntemleri", group="Uyum"),
            area("enclosure_references", "Ek referansları", group="Uyum"),
            area("compliance_statement", "Uyum beyanı", group="Uyum"),
            text("independent_checker", "Bağımsız kontrol mühendisi", group="Tarih ve Onay"),
            text("airworthiness_release", "Uçuşa elverişlilik yayımlayan", group="Tarih ve Onay"),
            day("release_date", "Yayın tarihi"),
        ),
    ),
    FormTemplate(
        "fm_dsg_0029e",
        "declaration-of-compliance",
        "Declaration of Compliance",
        "FM.DSG.0029E",
        "Declaration of Compliance",
        "Tip sertifikasyonu için uyum beyanı.",
        (
            text("document_number", "Doküman numarası", required=True),
            text("project", "Proje", required=True),
            text("aircraft", "Hava aracı"),
            area("certification_basis", "Sertifikasyon temeli", group="Uyum Beyanı"),
            area("type_design_reference", "Tip tasarımı referansı", group="Uyum Beyanı"),
            area(
                "airworthiness_requirements",
                "Uçuşa elverişlilik gereksinimleri",
                group="Uyum Beyanı",
            ),
            area("compliance_matrix_reference", "Uyum matrisi referansı", group="Uyum Beyanı"),
            area("risk_assessments", "Risk değerlendirmeleri", group="Uyum Beyanı"),
            area(
                "aircraft_schedule_inspection",
                "Hava aracı plan / muayene referansı",
                group="Uyum Beyanı",
            ),
            area("declaration_text", "Beyan metni", group="Uyum Beyanı"),
            day("declaration_date", "Beyan tarihi"),
            text("signer_name", "İmzalayan", group="Tarih ve Onay"),
            text("signer_title", "İmzalayan unvanı", group="Tarih ve Onay"),
        ),
    ),
    FormTemplate(
        "fm_dsg_0310e",
        "declaration-of-compliance",
        "Declaration of Compliance",
        "FM.DSG.0310E",
        "TUSAŞ Declaration of Compliance",
        "TUSAŞ tip sertifikasyonu uyum beyanı.",
        (
            text("project", "Proje", required=True),
            text("aircraft", "Hava aracı"),
            area("certification_basis", "Sertifikasyon temeli", group="Uyum Beyanı"),
            area("type_design_reference", "Tip tasarımı referansı", group="Uyum Beyanı"),
            area(
                "airworthiness_requirements",
                "Uçuşa elverişlilik gereksinimleri",
                group="Uyum Beyanı",
            ),
            area("compliance_matrix_reference", "Uyum matrisi referansı", group="Uyum Beyanı"),
            area("risk_assessments", "Risk değerlendirmeleri", group="Uyum Beyanı"),
            area(
                "aircraft_schedule_inspection",
                "Hava aracı plan / muayene referansı",
                group="Uyum Beyanı",
            ),
            area("declaration_text", "Beyan metni", group="Uyum Beyanı"),
            day("declaration_date", "Beyan tarihi"),
            text("signer_name", "İmzalayan", group="Tarih ve Onay"),
            text("signer_title", "İmzalayan unvanı", group="Tarih ve Onay"),
        ),
    ),
    FormTemplate(
        "fm_dsg_0327",
        "fcc",
        "FCC",
        "FM.DSG.0327",
        "Uçuş Uygunluk Belgesi / Flight Clearance Certificate",
        "Proje bazlı uçuş uygunluk belgesi kapak şablonu.",
        (
            text("project_name", "Proje adı", required=True),
            text("aircraft_type", "Hava aracı tipi"),
            text("aircraft_serial_number", "Hava aracı seri numarası"),
            text("flight_clearance_reference", "Uçuş uygunluk belgesi referansı"),
            area("certificate_summary", "Belge özeti", group="Belge Bilgileri"),
            *APPROVAL_FIELDS,
        ),
    ),
    FormTemplate(
        "fm_dsg_0008e",
        "assignment-management",
        "Görevlendirme Yönetimi",
        "FM.DSG.0008E",
        "Mission Letter for CVE",
        "CVE görevlendirme yazısı.",
        MISSION_FIELDS,
    ),
    FormTemplate(
        "fm_dsg_0009e",
        "assignment-management",
        "Görevlendirme Yönetimi",
        "FM.DSG.0009E",
        "Mission Letter for PCC",
        "PCC görevlendirme yazısı.",
        MISSION_FIELDS,
    ),
    FormTemplate(
        "fm_dsg_0010e",
        "assignment-management",
        "Görevlendirme Yönetimi",
        "FM.DSG.0010E",
        "Mission Letter for AS",
        "AS görevlendirme yazısı.",
        MISSION_FIELDS,
    ),
    FormTemplate(
        "fm_dsg_0011e",
        "assignment-management",
        "Görevlendirme Yönetimi",
        "FM.DSG.0011E",
        "Personnel Assessment Form for AS",
        "AS personel yeterlilik ve mülakat değerlendirmesi.",
        (
            text("paf_number", "PAF numarası", required=True),
            text("issue", "Yayın"),
            text("person_name", "Ad ve soyad", required=True),
            day("date_of_birth", "Doğum tarihi", group="Personel Bilgileri"),
            text("company_department", "Şirket ve bölüm", group="Personel Bilgileri"),
            text("title", "Unvan", group="Personel Bilgileri"),
            area("projects", "Projeler", group="Personel Bilgileri"),
            text("discipline", "Disiplin", group="Personel Bilgileri"),
            area("university_degree", "Üniversite derecesi", group="Yeterlilik"),
            area("experience", "Deneyim", group="Yeterlilik"),
            area("language_skills", "Dil bilgisi", group="Yeterlilik"),
            area("soft_skills", "Sosyal yetkinlikler", group="Yeterlilik"),
            area("training_history", "Eğitim geçmişi", group="Yeterlilik"),
            text("certification_exam_score", "Sertifikasyon sınav puanı", group="Yeterlilik"),
            text("technical_exam_score", "Teknik sınav puanı", group="Yeterlilik"),
            area("knowledge_assessment", "Bilgi ve süreç değerlendirmesi", group="Yeterlilik"),
            area("additional_remarks", "Ek açıklamalar", group="Değerlendirme"),
            area("interview_team", "Mülakat ekibi", group="Tarih ve Onay"),
            day("interview_date", "Mülakat tarihi"),
        ),
    ),
    FormTemplate(
        "fm_dsg_0120",
        "assignment-management",
        "Görevlendirme Yönetimi",
        "FM.DSG.0120",
        "Head of Design Authorisation",
        "Tasarım Başkanı yetkilendirme formu.",
        AUTHORIZATION_FIELDS,
    ),
    FormTemplate(
        "fm_dsg_0121e",
        "assignment-management",
        "Görevlendirme Yönetimi",
        "FM.DSG.0121E",
        "Head of Airworthiness Authorisation",
        "Uçuşa Elverişlilik Başkanı yetkilendirme formu.",
        AUTHORIZATION_FIELDS,
    ),
    FormTemplate(
        "fm_dsg_0281",
        "assignment-management",
        "Görevlendirme Yönetimi",
        "FM.DSG.0281",
        "Deputy Head of Design Authorisation",
        "Tasarım Başkan Yardımcısı yetkilendirme formu.",
        AUTHORIZATION_FIELDS,
    ),
    FormTemplate(
        "fm_dsg_0303e",
        "assignment-management",
        "Görevlendirme Yönetimi",
        "FM.DSG.0303E",
        "Deputy Head of Airworthiness Authorisation",
        "Uçuşa Elverişlilik Başkan Yardımcısı yetkilendirme formu.",
        AUTHORIZATION_FIELDS,
    ),
    FormTemplate(
        "fm_dsg_0007t",
        "haumik",
        "HAUMIK",
        "FM.DSG.0007T",
        "Hava Aracı Üzeri Mühendislik İnceleme Bulgu Formu",
        "Mühendislik inceleme bulgusu ve kapatma kararı.",
        (
            text("finding_number", "Bulgu numarası", required=True),
            day("finding_date", "GT tarihi"),
            text("project", "Proje"),
            area("finding_description", "Bulgu açıklaması", group="Bulgu"),
            area("root_cause", "Kök neden", group="Bulgu"),
            area("required_change", "Gerekli değişiklik", group="Bulgu"),
            text("initiator_department", "Başlatan / bölüm", group="Sorumlular"),
            text("system_design_responsible", "Sistem / tasarım sorumlusu", group="Sorumlular"),
            text("finding_responsible", "Bulgu sorumlusu", group="Sorumlular"),
            choice(
                "change_category",
                "Değişiklik kategorisi",
                (("i", "I"), ("ii", "II"), ("iii", "III"), ("iv", "IV"), ("v", "V"), ("vi", "VI")),
                group="Karar",
            ),
            day("start_date", "Başlatma tarihi", group="Karar"),
            area("board_decision", "Kurul kararı", group="Karar"),
            area("closure_decision", "Nihai karar / kapatma", group="Kapatma"),
            text("design_team_manager", "Mühendislik tasarım yöneticisi", group="Kapatma"),
            day("closure_date", "Kapatma tarihi", group="Kapatma"),
            area("photo_references", "Bulgu fotoğrafları / ekleri", group="Ekler"),
        ),
    ),
    FormTemplate(
        "fm_dsg_0378e",
        "loi",
        "LOI",
        "FM.DSG.0378E",
        "LOI Milestones",
        "Sertifikasyon fazlarına göre LoI kilometre taşları.",
        (
            text("project", "Proje", required=True),
            text("product", "Ürün / hava aracı"),
            text("type_certificate", "Tip sertifikası"),
            area("phase_1_milestones", "Faz 1 kilometre taşları", group="Kilometre Taşları"),
            area("phase_2_milestones", "Faz 2 kilometre taşları", group="Kilometre Taşları"),
            area("phase_3_milestones", "Faz 3 kilometre taşları", group="Kilometre Taşları"),
            area("notes", "Notlar", group="Kilometre Taşları"),
        ),
    ),
    FormTemplate(
        "fm_dsg_0379e",
        "loi",
        "LOI",
        "FM.DSG.0379E",
        "Level of Involvement (LOI)",
        "Gömülü LoI çalışma kitabı için kayıt ve özet formu.",
        (
            text("project", "Proje", required=True),
            text("certification_basis", "Sertifikasyon temeli"),
            text("loi_reference", "LoI referansı"),
            area("loi_summary", "LoI değerlendirme özeti", group="Değerlendirme"),
            area("workbook_notes", "Gömülü çalışma kitabı notları", group="Değerlendirme"),
            *APPROVAL_FIELDS,
        ),
    ),
    FormTemplate(
        "fm_qua_0388e",
        "others",
        "Others",
        "FM.QUA.0388E",
        "Candidate Auditor Evaluation",
        "Aday denetçi değerlendirme formu.",
        (
            text("candidate_name", "Aday denetçi adı ve soyadı", required=True),
            text("position", "Görevi"),
            text("department", "Departmanı"),
            text("audit_source", "Kaynak / puan"),
            day("audit_date", "Denetim tarihi"),
            area("planning_evaluation", "Planlama değerlendirmesi", group="Değerlendirme"),
            area(
                "audit_execution_evaluation",
                "Denetim yürütme değerlendirmesi",
                group="Değerlendirme",
            ),
            area("reporting_evaluation", "Raporlama değerlendirmesi", group="Değerlendirme"),
            area(
                "communication_evaluation",
                "İletişim ve davranış değerlendirmesi",
                group="Değerlendirme",
            ),
            choice(
                "decision",
                "Yeterlilik kararı",
                (("sufficient", "Yeterli"), ("insufficient", "Yetersiz")),
                group="Sonuç",
            ),
            area("remarks", "Açıklamalar", group="Sonuç"),
            text("evaluator_name", "Değerlendiren", group="Tarih ve Onay"),
        ),
    ),
    FormTemplate(
        "fm_qua_0579",
        "others",
        "Others",
        "FM.QUA.0579",
        "TUSAŞ Özel Uçuş İzni Başvuru Formu",
        "Özel uçuş izni başvurusu.",
        (
            *PTF_IDENTITY_FIELDS,
            day("intended_flight_date", "Öngörülen uçuş tarihi", group="Uçuş Bilgileri"),
            text("flight_duration", "Uçuş süresi", group="Uçuş Bilgileri"),
        ),
    ),
    FormTemplate(
        "fm_qua_0580",
        "others",
        "Others",
        "FM.QUA.0580",
        "Uçuş İzni İçin Uçuş Koşulları Onay Formu",
        "Uçuş koşulları onay formu.",
        (
            *PTF_IDENTITY_FIELDS,
            text("initial_approval_reference", "İlk onay referansı", group="Uçuş Bilgileri"),
            area("maintenance_instructions", "Talimatlar", group="Uçuş Bilgileri"),
            text("approval_name", "Onay makamı", group="Tarih ve Onay"),
        ),
    ),
    FormTemplate(
        "fm_qua_0581",
        "others",
        "Others",
        "FM.QUA.0581",
        "TUSAŞ Özel Uçuş İzni Onay Formu",
        "Özel uçuş izni onay formu.",
        (
            *PTF_IDENTITY_FIELDS,
            text("nationality_registration", "Hava aracı tescil işareti"),
            text("validity_period", "Geçerlilik süresi", group="Uçuş Bilgileri"),
            text("place_of_issue", "Yayın yeri", group="Tarih ve Onay"),
            text("authority_signer", "Otorite yetkilisi", group="Tarih ve Onay"),
        ),
    ),
    FormTemplate(
        "fm_qua_0701t",
        "others",
        "Others",
        "FM.QUA.0701T",
        "Hava Aracı Olay İnceleme Raporu",
        "Hava aracı olay inceleme ve düzeltici faaliyet raporu.",
        (
            text("report_number", "Olay inceleme rapor numarası", required=True),
            text("project_name", "Proje adı"),
            text("aircraft_model", "Hava aracı modeli"),
            text("aircraft_serial_number", "Hava aracı seri numarası"),
            text("equipment_name", "Ekipman / parça adı", group="Ekipman Bilgileri"),
            text("part_number", "Parça numarası", group="Ekipman Bilgileri"),
            text("equipment_serial_number", "Ekipman seri numarası", group="Ekipman Bilgileri"),
            text("damage_location", "Hasar bölgesi", group="Ekipman Bilgileri"),
            text("event_datetime", "Olay tarihi ve saati", group="Olay Bilgileri"),
            text("event_location", "Olay yeri", group="Olay Bilgileri"),
            area("event_description", "Olayın açıklaması", group="Olay Bilgileri"),
            text("occurrence_category", "Olay kategorisi", group="Olay Bilgileri"),
            area("investigation", "İnceleme", group="İnceleme"),
            area("root_cause", "Olayın kök sebebi", group="İnceleme"),
            area("findings", "Tespit edilen diğer hususlar", group="İnceleme"),
            area("preventive_actions", "Önlem, öneri ve tavsiyeler", group="İnceleme"),
            area("attachments", "Ekler", group="İnceleme"),
            *APPROVAL_FIELDS,
        ),
    ),
    FormTemplate(
        "fm_dsg_0200t",
        "panel-declaration",
        "Panel Uyum Beyanı",
        "FM.DSG.0200T",
        "Panel Uyum Beyanı",
        "Panel bazlı uyum ve sertifikasyon beyanı.",
        (
            text("panel_name", "Panel adı", required=True),
            text("project_name", "Proje adı", required=True),
            area("related_documents", "İlgili dokümanlar", group="Dokümanlar"),
            area("compliance_documents", "Uyum dokümanları", group="Dokümanlar"),
            area(
                "certification_actions", "Sertifikasyon aksiyonları / sınırlamalar", group="Beyan"
            ),
            area("declaration", "Panel beyanı", group="Beyan"),
            area("configuration_basis", "Konfigürasyon temeli", group="Beyan"),
            text("panel_coordinator", "Panel koordinatörü", group="Tarih ve Onay"),
            area("panel_members", "Panel üyeleri", group="Tarih ve Onay"),
            day("declaration_date", "Beyan tarihi"),
        ),
    ),
    FormTemplate(
        "fm_dsg_0006e",
        "reportable-occurrence",
        "Reportable Occurrence Form",
        "FM.DSG.0006E",
        "Reportable Occurrence Form",
        "Raporlanabilir olay ve uçuşa elverişlilik etkisi kaydı.",
        (
            text("report_number", "Raporlanabilir olay form numarası", required=True),
            text("project_name", "Proje adı"),
            text("aircraft_model", "Hava aracı modeli"),
            text("aircraft_version", "Hava aracı versiyonu"),
            text("aircraft_serial_number", "Hava aracı seri numarası"),
            text("equipment_name", "Ekipman / parça adı", group="Ekipman Bilgileri"),
            text("part_number", "Parça numarası", group="Ekipman Bilgileri"),
            text("equipment_serial_number", "Ekipman seri numarası", group="Ekipman Bilgileri"),
            text("defect_location", "Kusur konumu", group="Ekipman Bilgileri"),
            area("assembly_information", "Montaj bilgileri", group="Ekipman Bilgileri"),
            text("occurrence_datetime", "Olay tarihi ve saati", group="Olay Bilgileri"),
            text("occurrence_location", "Olay yeri", group="Olay Bilgileri"),
            area("occurrence_description", "Olay açıklaması", group="Olay Bilgileri"),
            area("airworthiness_impact", "Uçuşa elverişlilik etkisi", group="Olay Bilgileri"),
            area("short_term_action", "Kısa vadeli aksiyon", group="Aksiyonlar"),
            area("attachments", "Ekler", group="Aksiyonlar"),
            text("submitted_by", "Gönderen", group="Tarih ve Onay"),
            day("submission_date", "Gönderim tarihi"),
            text("contact_information", "İletişim bilgileri", group="Tarih ve Onay"),
        ),
    ),
    FormTemplate(
        "fm_dsg_0465e",
        "tc-procedures",
        "TC Procedures",
        "FM.DSG.0465E",
        "Certification Review Item",
        "Sertifikasyon inceleme maddesi (CRI) formu.",
        (
            text("document_number", "Doküman numarası", required=True),
            text("addressee", "Muhatap"),
            text("subject", "Konu", required=True),
            text("project", "Proje"),
            text("cri_number", "CRI numarası", required=True),
            text("requirement", "Gereksinim"),
            text("issue_number", "Yayın numarası"),
            text("advisory_material", "Tavsiye materyali"),
            day("issue_date", "Yayın tarihi"),
            choice(
                "status", "Durum", (("open", "Open"), ("closed", "Closed")), group="CRI Bilgileri"
            ),
            text("category", "Kategori", group="CRI Bilgileri"),
            text("next_action_by", "Sonraki aksiyon sahibi", group="CRI Bilgileri"),
            text("primary_panel", "Birincil panel", group="CRI Bilgileri"),
            day("closure_target", "Hedef kapanış tarihi", group="CRI Bilgileri"),
            area("secondary_panels", "İkincil paneller", group="CRI Bilgileri"),
            area("statement_of_issue", "Konu beyanı", group="Değerlendirme"),
            area("discussion", "Değerlendirme / tartışma", group="Değerlendirme"),
            area("authority_positions", "Otorite pozisyonları", group="Değerlendirme"),
            area("conclusion", "Sonuç", group="Sonuç"),
            text("conclusion_authority", "Sonuç otoritesi", group="Sonuç"),
            text("conclusion_name", "Sonuç imzalayan", group="Sonuç"),
            day("conclusion_date", "Sonuç tarihi", group="Sonuç"),
            area("acceptable_means", "Kabul edilebilir uyum yöntemleri", group="Ekler"),
            area(
                "panel_responsibilities", "Panel sorumlulukları ve uyum dokümanları", group="Ekler"
            ),
            area("special_conditions", "Özel koşullar", group="Ekler"),
            area("change_records", "Değişiklik kayıtları", group="Ekler"),
        ),
    ),
)

FORM_TEMPLATE_BY_CODE = {template.code: template for template in FORM_TEMPLATES}


class FormTemplateValidationError(ValueError):
    def __init__(self, errors: dict[str, list[str]]):
        super().__init__("Form alanları geçersiz.")
        self.errors = errors


def get_form_template(code: str) -> FormTemplate:
    try:
        return FORM_TEMPLATE_BY_CODE[code]
    except KeyError as exc:
        raise FormTemplateValidationError(
            {"template_code": ["Geçerli bir FM form şablonu seçilmelidir."]}
        ) from exc


def validate_form_data(template_code: str, data: Any) -> dict[str, Any]:
    template = get_form_template(template_code)
    if not isinstance(data, dict):
        raise FormTemplateValidationError(
            {"data": ["Form alanları nesne biçiminde gönderilmelidir."]}
        )
    if len(str(data)) > 250_000:
        raise FormTemplateValidationError({"data": ["Form verisi izin verilen sınırı aşıyor."]})

    field_by_key = {field.key: field for field in template.fields}
    errors: dict[str, list[str]] = {}
    unknown_fields = sorted(set(data) - set(field_by_key))
    if unknown_fields:
        errors["data"] = [
            f"Seçilen formda bulunmayan alanlar gönderildi: {', '.join(unknown_fields)}"
        ]

    cleaned: dict[str, Any] = {}
    for key, field in field_by_key.items():
        value = data.get(key)
        if field.field_type in {"text", "textarea", "date", "select"}:
            if value is None:
                value = ""
            if not isinstance(value, str):
                errors[key] = ["Metin değeri gönderilmelidir."]
                continue
            value = value.strip()
            if field.required and not value:
                errors[key] = [f"{field.label} zorunludur."]
            elif len(value) > field.max_length:
                errors[key] = [f"En fazla {field.max_length} karakter girilebilir."]
            elif field.field_type == "date" and value:
                try:
                    date.fromisoformat(value)
                except ValueError:
                    errors[key] = ["Geçerli bir tarih gönderilmelidir."]
            elif field.field_type == "select" and value not in {item[0] for item in field.options}:
                errors[key] = ["Geçerli bir seçim yapılmalıdır."]
        cleaned[key] = value

    if errors:
        raise FormTemplateValidationError(errors)
    return cleaned


def form_process_catalog() -> list[dict[str, Any]]:
    processes: dict[str, dict[str, Any]] = {}
    for template in FORM_TEMPLATES:
        process = processes.setdefault(
            template.process_code,
            {"code": template.process_code, "name": template.process_name, "templates": []},
        )
        process["templates"].append(template.as_dict())
    return list(processes.values())
