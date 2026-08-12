from django.db import models


class FlightPurpose(models.TextChoices):
    RESEARCH_DEVELOPMENT = "research_development", "Geliştirme"
    CERTIFICATION_COMPLIANCE = "certification_compliance", "Tasarım ya da üretim kuruluşlarının personel eğitimi"
    PRODUCTION_FLIGHT_TEST = "production_flight_test", "Üretim tesisleri arasında hava aracının uçurulması"
    CUSTOMER_ACCEPTANCE = "customer_acceptance", "Müşteri kabulü için uçurulması"
    MAINTENANCE_CHECK = "maintenance_check", "Uçak teslimatı ve ihracı"
    DEMONSTRATION = "demonstration", "Bakım veya uçuşa elverişlilik incelenmesi için ya da depolama yerine uçurulması"


FLIGHT_PURPOSE_LABELS = dict(FlightPurpose.choices)


def flight_purpose_labels(values):
    return [FLIGHT_PURPOSE_LABELS[value] for value in values if value in FLIGHT_PURPOSE_LABELS]
