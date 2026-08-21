"""Narrow cross-feature selectors for the operational calendar."""

from datetime import date

from ..form_processes.selectors import approved_flight_permit_operational_alert_candidates
from ..technical_documents.selectors import technical_document_operational_alert_candidates


def operational_alert_candidates(*, as_of: date, horizon_days: int):
    return (
        technical_document_operational_alert_candidates(
            as_of=as_of,
            horizon_days=horizon_days,
        ),
        approved_flight_permit_operational_alert_candidates(),
    )
