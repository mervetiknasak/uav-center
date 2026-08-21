from .models import FormProcessRecord


def form_process_records_with_actors():
    return FormProcessRecord.objects.select_related("created_by", "updated_by")


def approved_flight_permit_operational_alert_candidates():
    """Return approved flight permits using the migrated form-record contract."""

    return (
        FormProcessRecord.objects.filter(
            process_code="flight-permits",
            status=FormProcessRecord.STATUS_APPROVED,
            data__permit_lifecycle_status="approved",
        )
        .only("id", "record_number", "title", "data")
        .order_by("pk")
    )
