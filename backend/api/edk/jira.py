"""Build editable Jira drafts from meeting minutes and publish them."""

from __future__ import annotations

import hashlib
import logging
import re
from collections.abc import Mapping, Sequence
from typing import Any, Protocol

from django.conf import settings

from ..common.redaction import safe_exception_message
from ..organization.models import PanelResponsible
from ..services.jira_connector import JiraConnectorError

MEETING_FIELDS = (
    ("project", "Proje"),
    ("subject", "Konu"),
    ("mom_no", "Tutanak No"),
    ("revision", "Revizyon"),
    ("date_time", "Tarih / Saat"),
    ("location", "Toplantı Yeri"),
    ("agenda", "Gündem"),
    ("discussions_decisions", "Görüşmeler ve kararlar"),
)
logger = logging.getLogger(__name__)


class JiraDraftPublisher(Protocol):
    """Narrow Jira surface required to publish one meeting-minute draft."""

    @property
    def server_url(self) -> str: ...

    def search_issues(
        self,
        jql: str,
        *,
        max_results: int | bool = 50,
        fields: str | Sequence[str] = "*all",
    ) -> Sequence[Any]: ...

    def create_issue(
        self,
        *,
        project_key: str,
        summary: str,
        issue_type: str,
        description: str | None = None,
        assignee_username: str | None = None,
        labels: Sequence[str] | None = None,
        parent_key: str | None = None,
        custom_fields: Mapping[str, Any] | None = None,
    ) -> Any: ...


def _slug(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return value[:100]


def build_jira_draft(extracted: dict[str, Any]) -> dict[str, Any]:
    people = list(PanelResponsible.objects.exclude(username=""))
    by_name = {person.name.casefold().strip(): person.username for person in people}
    subject = (extracted.get("subject") or "").strip()
    mom_no = (extracted.get("mom_no") or "").strip()
    fingerprint_source = "|".join(str(extracted.get(key) or "") for key, _label in MEETING_FIELDS)
    fingerprint = (
        _slug(mom_no) or hashlib.sha256(fingerprint_source.encode("utf-8")).hexdigest()[:16]
    )
    duplicate_label = f"meeting-minutes-{fingerprint}"

    meeting_fields = [
        {
            "key": key,
            "label": label,
            "value": str(extracted.get(key) or ""),
            "enabled": bool(extracted.get(key)),
        }
        for key, label in MEETING_FIELDS
    ]
    subtasks = []
    for index, item in enumerate(extracted.get("action_items") or []):
        responsible = (item.get("responsible") or "").strip()
        subtasks.append(
            {
                "client_id": f"action-{index + 1}",
                "enabled": True,
                "summary": (item.get("action_item") or "").strip(),
                "description": f"Toplantı aksiyon no: {item.get('no') or index + 1}",
                "responsible": responsible,
                "username": by_name.get(responsible.casefold()),
                "due_date": (item.get("due_date") or "").strip(),
            }
        )

    return {
        "task": {
            "project_key": settings.JIRA_MEETING_PROJECT_KEY,
            "issue_type": "Task",
            "summary": subject or f"Toplantı tutanağı {mom_no}".strip(),
            "meeting_fields": meeting_fields,
            "labels": ["meeting-minutes", duplicate_label],
        },
        "subtasks": subtasks,
        "warnings": [
            warning
            for warning in (
                (
                    "Bazı sorumlular için username eşleşmesi bulunamadı."
                    if any(item["responsible"] and not item["username"] for item in subtasks)
                    else None
                ),
            )
            if warning
        ],
    }


def _description(fields: list[dict[str, Any]]) -> str:
    return "\n\n".join(
        f"{field.get('label', field.get('key', 'Alan'))}\n{field.get('value', '')}"
        for field in fields
        if field.get("enabled", True) and str(field.get("value", "")).strip()
    )


def _issue_result(issue: Any, server: str) -> dict[str, str]:
    key = str(issue.key)
    return {"key": key, "url": f"{server.rstrip('/')}/browse/{key}"}


def publish_jira_draft(
    payload: dict[str, Any],
    *,
    jira: JiraDraftPublisher,
) -> dict[str, Any]:
    task = payload["task"]
    project_key = task["project_key"].strip()
    labels = [str(label).strip() for label in task.get("labels", []) if str(label).strip()]
    duplicate_label = next(
        (label for label in labels if label.startswith("meeting-minutes-")), None
    )
    existing_parent = None
    if duplicate_label:
        existing = jira.search_issues(
            f'project = "{project_key}" AND labels = "{duplicate_label}"',
            max_results=1,
            fields=["key"],
        )
        if existing:
            existing_parent = existing[0]

    parent_issue = existing_parent or jira.create_issue(
        project_key=project_key,
        summary=task["summary"].strip(),
        issue_type=task.get("issue_type") or "Task",
        description=_description(task.get("meeting_fields", [])),
        labels=labels,
    )
    parent = _issue_result(parent_issue, jira.server_url)
    results = []
    for item in payload.get("subtasks", []):
        if not item.get("enabled", True):
            continue
        try:
            action_label = f"meeting-action-{_slug(str(item.get('client_id') or 'item'))}"
            if existing_parent:
                existing_subtasks = jira.search_issues(
                    f'parent = "{parent["key"]}" AND labels = "{action_label}"',
                    max_results=1,
                    fields=["key"],
                )
                if existing_subtasks:
                    results.append(
                        {
                            "client_id": item.get("client_id"),
                            "status": "skipped",
                            **_issue_result(existing_subtasks[0], jira.server_url),
                        }
                    )
                    continue
            custom_fields = {}
            if str(item.get("due_date") or "").strip():
                custom_fields["duedate"] = str(item["due_date"]).strip()
            issue = jira.create_issue(
                project_key=project_key,
                summary=str(item["summary"]).strip(),
                issue_type="Sub-task",
                description=str(item.get("description") or "").strip() or None,
                assignee_username=str(item.get("username") or "").strip() or None,
                parent_key=parent["key"],
                labels=["meeting-action", action_label],
                custom_fields=custom_fields,
            )
            results.append(
                {
                    "client_id": item.get("client_id"),
                    "status": "created",
                    **_issue_result(issue, jira.server_url),
                }
            )
        except (JiraConnectorError, KeyError, ValueError) as exc:
            logger.error(
                "Jira subtask publish failed: %s",
                safe_exception_message(exc),
                extra={"event": "jira_subtask_publish_failed"},
            )
            results.append(
                {
                    "client_id": item.get("client_id"),
                    "status": "error",
                    "error": "Alt görev Jira'ya aktarılamadı.",
                }
            )
    return {
        "status": "existing" if existing_parent else "created",
        "message": (
            "Mevcut Task kullanıldı; eksik Sub-task'lar işlendi." if existing_parent else ""
        ),
        "task": parent,
        "subtasks": results,
    }
