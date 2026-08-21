"""Build the read-only operational calendar from existing domain records."""

from collections.abc import Mapping
from datetime import date

from django.utils import timezone

from .selectors import operational_alert_candidates

CRITICAL_DAYS = 7
HORIZON_DAYS = 30
STALE_DAYS = 14

_DUE_TERMINAL_STATUSES = {"published", "superseded", "archived"}
_REVIEW_TERMINAL_STATUSES = {"superseded", "archived"}
_WORKFLOW_STATUSES = {"in_review", "changes_requested"}

_BUCKET_ORDER = {
    "overdue": 0,
    "next_7_days": 1,
    "next_30_days": 2,
    "stale": 3,
}


def _date_bucket(days_remaining: int) -> str | None:
    if days_remaining < 0:
        return "overdue"
    if days_remaining <= CRITICAL_DAYS:
        return "next_7_days"
    if days_remaining <= HORIZON_DAYS:
        return "next_30_days"
    return None


def _project(document):
    return {
        "id": document.project_id,
        "code": document.project.code,
        "name": document.project.name,
    }


def _panels(document):
    return [{"id": panel.pk, "name": panel.name} for panel in document.panels.all()]


def _technical_document_date_alert(
    document,
    *,
    alert_type: str,
    alert_date: date,
    as_of: date,
    can_notify: bool,
):
    days_remaining = (alert_date - as_of).days
    bucket = _date_bucket(days_remaining)
    if bucket is None:
        return None
    return {
        "key": f"technical_document:{document.pk}:{alert_type}",
        "source_type": "technical_document",
        "source_id": document.pk,
        "alert_type": alert_type,
        "bucket": bucket,
        "date": alert_date,
        "days_remaining": days_remaining,
        "days_in_status": None,
        "reference": document.code,
        "title": document.title,
        "status": document.status,
        "status_display": document.get_status_display(),
        "priority": document.priority,
        "project": _project(document),
        "panels": _panels(document),
        "can_notify": can_notify,
    }


def _technical_document_workflow_alert(document, *, as_of: date, can_notify: bool):
    status_started_at = document.current_status_started_at
    if status_started_at is None:
        return None
    status_started_on = timezone.localdate(status_started_at)
    days_in_status = (as_of - status_started_on).days
    if days_in_status < STALE_DAYS:
        return None
    return {
        "key": f"technical_document:{document.pk}:workflow_stale",
        "source_type": "technical_document",
        "source_id": document.pk,
        "alert_type": "workflow_stale",
        "bucket": "stale",
        "date": status_started_on,
        "days_remaining": None,
        "days_in_status": days_in_status,
        "reference": document.code,
        "title": document.title,
        "status": document.status,
        "status_display": document.get_status_display(),
        "priority": document.priority,
        "project": _project(document),
        "panels": _panels(document),
        "can_notify": can_notify,
    }


def _parse_iso_date(value) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _flight_permit_alert(record, *, as_of: date):
    if not isinstance(record.data, Mapping):
        return None
    valid_until = _parse_iso_date(record.data.get("valid_until"))
    if valid_until is None:
        return None
    days_remaining = (valid_until - as_of).days
    bucket = _date_bucket(days_remaining)
    if bucket is None:
        return None
    return {
        "key": f"flight_permit:{record.pk}:valid_until",
        "source_type": "flight_permit",
        "source_id": record.pk,
        "alert_type": "valid_until",
        "bucket": bucket,
        "date": valid_until,
        "days_remaining": days_remaining,
        "days_in_status": None,
        "reference": record.record_number,
        "title": record.title,
        "status": "approved",
        "status_display": "Onaylandı",
        "priority": None,
        "project": None,
        "panels": [],
        "can_notify": False,
    }


def _alert_sort_key(alert):
    urgency = (
        alert["days_remaining"] if alert["days_remaining"] is not None else -alert["days_in_status"]
    )
    return (
        _BUCKET_ORDER[alert["bucket"]],
        urgency,
        alert["source_type"],
        alert["reference"].casefold(),
        alert["alert_type"],
        alert["source_id"],
    )


def build_operational_alerts(*, as_of: date, is_staff: bool):
    technical_documents, flight_permits = operational_alert_candidates(
        as_of=as_of,
        horizon_days=HORIZON_DAYS,
    )
    alerts = []
    for document in technical_documents:
        if document.due_date is not None and document.status not in _DUE_TERMINAL_STATUSES:
            alert = _technical_document_date_alert(
                document,
                alert_type="due_date",
                alert_date=document.due_date,
                as_of=as_of,
                can_notify=is_staff,
            )
            if alert is not None:
                alerts.append(alert)
        if document.review_date is not None and document.status not in _REVIEW_TERMINAL_STATUSES:
            alert = _technical_document_date_alert(
                document,
                alert_type="review_date",
                alert_date=document.review_date,
                as_of=as_of,
                can_notify=is_staff,
            )
            if alert is not None:
                alerts.append(alert)
        if document.status in _WORKFLOW_STATUSES:
            alert = _technical_document_workflow_alert(
                document,
                as_of=as_of,
                can_notify=is_staff,
            )
            if alert is not None:
                alerts.append(alert)

    for record in flight_permits:
        alert = _flight_permit_alert(record, as_of=as_of)
        if alert is not None:
            alerts.append(alert)

    alerts.sort(key=_alert_sort_key)
    summary = {
        "total": len(alerts),
        "overdue": 0,
        "next_7_days": 0,
        "next_30_days": 0,
        "stale": 0,
    }
    for alert in alerts:
        summary[alert["bucket"]] += 1

    return {
        "as_of": as_of,
        "thresholds": {
            "critical_days": CRITICAL_DAYS,
            "horizon_days": HORIZON_DAYS,
            "stale_days": STALE_DAYS,
        },
        "summary": summary,
        "alerts": alerts,
    }
