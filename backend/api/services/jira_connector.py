"""Reusable Jira integration built on top of the ``jira`` Python package."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Mapping, Sequence

from django.conf import settings


class JiraConnectorError(RuntimeError):
    """Normalized error raised for Jira client and API failures."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        url: str | None = None,
        response_text: str | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.url = url
        self.response_text = response_text


@dataclass(frozen=True)
class JiraConfig:
    server: str
    email: str = ""
    api_token: str = ""
    username: str = ""
    password: str = ""
    personal_access_token: str = ""
    verify_ssl: bool = True
    timeout: int = 30

    @classmethod
    def from_settings(cls) -> "JiraConfig":
        return cls(
            server=getattr(settings, "JIRA_SERVER", ""),
            email=getattr(settings, "JIRA_EMAIL", ""),
            api_token=getattr(settings, "JIRA_API_TOKEN", ""),
            username=getattr(settings, "JIRA_USERNAME", ""),
            password=getattr(settings, "JIRA_PASSWORD", ""),
            personal_access_token=getattr(settings, "JIRA_PERSONAL_ACCESS_TOKEN", ""),
            verify_ssl=getattr(settings, "JIRA_VERIFY_SSL", True),
            timeout=getattr(settings, "JIRA_TIMEOUT", 30),
        )

    def validate(self) -> None:
        if not self.server:
            raise JiraConnectorError("JIRA_SERVER tanımlanmalıdır.")
        if not (
            (self.email and self.api_token)
            or (self.username and self.password)
            or self.personal_access_token
        ):
            raise JiraConnectorError(
                "Jira kimlik bilgisi eksik. E-posta/API token, kullanıcı/parola "
                "veya personal access token tanımlayın."
            )


class JiraConnector:
    """A broad, framework-friendly façade over :class:`jira.JIRA`.

    Methods intentionally return Jira resource objects. Callers can therefore
    use every field exposed by the upstream library without this connector
    silently discarding data.
    """

    def __init__(
        self,
        config: JiraConfig | None = None,
        *,
        client: Any | None = None,
    ):
        self.config = config or JiraConfig.from_settings()
        self._client = client
        if client is None:
            self.config.validate()

    @property
    def client(self) -> Any:
        if self._client is None:
            self._client = self._build_client()
        return self._client

    def _build_client(self) -> Any:
        try:
            from jira import JIRA
        except ImportError as exc:
            raise JiraConnectorError(
                "Jira connector için 'jira' Python paketi kurulu olmalıdır."
            ) from exc

        options = {
            "server": self.config.server.rstrip("/"),
            "verify": self.config.verify_ssl,
        }
        kwargs: dict[str, Any] = {
            "options": options,
            "timeout": self.config.timeout,
        }
        if self.config.personal_access_token:
            kwargs["token_auth"] = self.config.personal_access_token
        elif self.config.email and self.config.api_token:
            kwargs["basic_auth"] = (self.config.email, self.config.api_token)
        else:
            kwargs["basic_auth"] = (self.config.username, self.config.password)

        try:
            return JIRA(**kwargs)
        except Exception as exc:
            raise self._normalize_error(exc, "Jira bağlantısı kurulamadı") from exc

    def _execute(self, action: str, operation: Any, *args: Any, **kwargs: Any) -> Any:
        try:
            return operation(*args, **kwargs)
        except JiraConnectorError:
            raise
        except Exception as exc:
            raise self._normalize_error(exc, action) from exc

    @staticmethod
    def _normalize_error(exc: Exception, action: str) -> JiraConnectorError:
        response = getattr(exc, "response", None)
        status_code = _first_value(
            getattr(exc, "status_code", None),
            getattr(response, "status_code", None),
        )
        url = _first_value(
            getattr(exc, "url", None),
            getattr(response, "url", None),
        )
        details = _extract_error_details(exc, response)
        response_text = "; ".join(details) if details else None
        message = f"{action} başarısız"
        if status_code:
            message += f" (HTTP {status_code})"
        if response_text:
            message += f": {response_text}"
        return JiraConnectorError(
            message,
            status_code=status_code,
            url=url,
            response_text=response_text,
        )

    # Connection and metadata
    def check_connection(self) -> Any:
        return self._execute("Jira bağlantı kontrolü", self.client.myself)

    def server_info(self) -> Mapping[str, Any]:
        return self._execute("Jira sunucu bilgisi alınması", self.client.server_info)

    def fields(self) -> Sequence[Mapping[str, Any]]:
        return self._execute("Jira alanlarının listelenmesi", self.client.fields)

    def priorities(self) -> Sequence[Any]:
        return self._execute("Önceliklerin listelenmesi", self.client.priorities)

    def issue_types(self) -> Sequence[Any]:
        return self._execute("Issue tiplerinin listelenmesi", self.client.issue_types)

    def statuses(self) -> Sequence[Any]:
        return self._execute("Durumların listelenmesi", self.client.statuses)

    # Projects, versions and components
    def projects(self) -> Sequence[Any]:
        return self._execute("Projelerin listelenmesi", self.client.projects)

    def project(self, project_key: str) -> Any:
        return self._execute("Projenin alınması", self.client.project, project_key)

    def project_versions(self, project_key: str) -> Sequence[Any]:
        return self._execute(
            "Proje sürümlerinin listelenmesi",
            self.client.project_versions,
            project_key,
        )

    def create_version(
        self,
        name: str,
        project_key: str,
        *,
        description: str | None = None,
        release_date: str | None = None,
        start_date: str | None = None,
        released: bool = False,
        archived: bool = False,
    ) -> Any:
        kwargs = _without_none(
            {
                "description": description,
                "releaseDate": release_date,
                "startDate": start_date,
                "released": released,
                "archived": archived,
            }
        )
        return self._execute(
            "Sürüm oluşturma",
            self.client.create_version,
            name,
            project_key,
            **kwargs,
        )

    def project_components(self, project_key: str) -> Sequence[Any]:
        return self._execute(
            "Proje bileşenlerinin listelenmesi",
            self.client.project_components,
            project_key,
        )

    def create_component(
        self,
        name: str,
        project_key: str,
        *,
        description: str | None = None,
        lead_user_name: str | None = None,
        assignee_type: str | None = None,
    ) -> Any:
        return self._execute(
            "Bileşen oluşturma",
            self.client.create_component,
            name,
            project_key,
            **_without_none(
                {
                    "description": description,
                    "leadUserName": lead_user_name,
                    "assigneeType": assignee_type,
                }
            ),
        )

    # Users and groups
    def search_users(
        self,
        query: str,
        *,
        start_at: int = 0,
        max_results: int = 50,
        include_active: bool = True,
        include_inactive: bool = False,
    ) -> Sequence[Any]:
        return self._execute(
            "Kullanıcı arama",
            self.client.search_users,
            query=query,
            startAt=start_at,
            maxResults=max_results,
            includeActive=include_active,
            includeInactive=include_inactive,
        )

    def group_members(self, group_name: str) -> Mapping[str, Any]:
        return self._execute(
            "Grup üyelerinin listelenmesi",
            self.client.group_members,
            group_name,
        )

    # Issue retrieval and search
    def issue(
        self,
        issue_key: str,
        *,
        fields: str | Sequence[str] | None = None,
        expand: str | None = None,
    ) -> Any:
        kwargs = _without_none({"fields": fields, "expand": expand})
        return self._execute("Issue alınması", self.client.issue, issue_key, **kwargs)

    def search_issues(
        self,
        jql: str,
        *,
        start_at: int = 0,
        max_results: int | bool = 50,
        fields: str | Sequence[str] = "*all",
        expand: str | None = None,
        validate_query: bool = True,
    ) -> Sequence[Any]:
        return self._execute(
            "Issue arama",
            self.client.search_issues,
            jql,
            startAt=start_at,
            maxResults=max_results,
            fields=fields,
            expand=expand,
            validate_query=validate_query,
        )

    # Issue mutations
    def create_issue(
        self,
        *,
        project_key: str,
        summary: str,
        issue_type: str,
        description: str | None = None,
        assignee: str | None = None,
        priority: str | None = None,
        labels: Sequence[str] | None = None,
        components: Sequence[str] | None = None,
        parent_key: str | None = None,
        custom_fields: Mapping[str, Any] | None = None,
        prefetch: bool = True,
    ) -> Any:
        fields: dict[str, Any] = {
            "project": {"key": project_key},
            "summary": summary,
            "issuetype": {"name": issue_type},
        }
        fields.update(
            _without_none(
                {
                    "description": description,
                    "assignee": {"accountId": assignee} if assignee else None,
                    "priority": {"name": priority} if priority else None,
                    "labels": list(labels) if labels is not None else None,
                    "components": (
                        [{"name": component} for component in components]
                        if components is not None
                        else None
                    ),
                    "parent": {"key": parent_key} if parent_key else None,
                }
            )
        )
        fields.update(custom_fields or {})
        return self._execute(
            "Issue oluşturma",
            self.client.create_issue,
            fields=fields,
            prefetch=prefetch,
        )

    def create_issues(
        self,
        field_list: Sequence[Mapping[str, Any]],
        *,
        prefetch: bool = True,
    ) -> Sequence[Any]:
        return self._execute(
            "Toplu issue oluşturma",
            self.client.create_issues,
            field_list=list(field_list),
            prefetch=prefetch,
        )

    def update_issue(
        self,
        issue_key: str,
        *,
        fields: Mapping[str, Any] | None = None,
        update: Mapping[str, Any] | None = None,
        notify_users: bool = True,
    ) -> Any:
        issue = self.issue(issue_key)
        kwargs = _without_none({"fields": fields, "update": update})
        kwargs["notify"] = notify_users
        self._execute("Issue güncelleme", issue.update, **kwargs)
        return issue

    def delete_issue(self, issue_key: str, *, delete_subtasks: bool = False) -> None:
        issue = self.issue(issue_key)
        self._execute(
            "Issue silme",
            issue.delete,
            deleteSubtasks=delete_subtasks,
        )

    def assign_issue(self, issue_key: str, assignee: str | None) -> bool:
        return self._execute(
            "Issue atama",
            self.client.assign_issue,
            issue_key,
            assignee,
        )

    def transitions(self, issue_key: str, *, expand: str | None = None) -> Sequence[Any]:
        return self._execute(
            "Issue geçişlerinin listelenmesi",
            self.client.transitions,
            issue_key,
            expand=expand,
        )

    def transition_issue(
        self,
        issue_key: str,
        transition: str | int,
        *,
        fields: Mapping[str, Any] | None = None,
        comment: str | None = None,
    ) -> None:
        kwargs: dict[str, Any] = {"fields": dict(fields or {})}
        if comment:
            kwargs["comment"] = comment
        self._execute(
            "Issue durum geçişi",
            self.client.transition_issue,
            issue_key,
            transition,
            **kwargs,
        )

    # Comments, attachments, worklogs and links
    def comments(self, issue_key: str) -> Sequence[Any]:
        return self._execute(
            "Yorumların listelenmesi",
            self.client.comments,
            issue_key,
        )

    def add_comment(
        self,
        issue_key: str,
        body: str,
        *,
        visibility: Mapping[str, str] | None = None,
    ) -> Any:
        return self._execute(
            "Yorum ekleme",
            self.client.add_comment,
            issue_key,
            body,
            visibility=visibility,
        )

    def update_comment(self, issue_key: str, comment_id: str, body: str) -> Any:
        comment = self._execute(
            "Yorumun alınması",
            self.client.comment,
            issue_key,
            comment_id,
        )
        self._execute("Yorum güncelleme", comment.update, body=body)
        return comment

    def delete_comment(self, issue_key: str, comment_id: str) -> None:
        comment = self._execute(
            "Yorumun alınması",
            self.client.comment,
            issue_key,
            comment_id,
        )
        self._execute("Yorum silme", comment.delete)

    def add_attachment(
        self,
        issue_key: str,
        attachment: str | Path | Any,
        *,
        filename: str | None = None,
    ) -> Any:
        if isinstance(attachment, (str, Path)):
            path = Path(attachment)
            if not path.is_file():
                raise JiraConnectorError(f"Ek dosyası bulunamadı: {path}")
            attachment = str(path)
        return self._execute(
            "Dosya eki ekleme",
            self.client.add_attachment,
            issue=issue_key,
            attachment=attachment,
            filename=filename,
        )

    def worklogs(self, issue_key: str) -> Sequence[Any]:
        return self._execute(
            "Worklog kayıtlarının listelenmesi",
            self.client.worklogs,
            issue_key,
        )

    def add_worklog(
        self,
        issue_key: str,
        time_spent: str,
        *,
        comment: str | None = None,
        started: str | None = None,
        new_estimate: str | None = None,
        reduce_by: str | None = None,
        adjust_estimate: str = "auto",
    ) -> Any:
        return self._execute(
            "Worklog ekleme",
            self.client.add_worklog,
            issue_key,
            timeSpent=time_spent,
            **_without_none(
                {
                    "comment": comment,
                    "started": started,
                    "newEstimate": new_estimate,
                    "reduceBy": reduce_by,
                    "adjustEstimate": adjust_estimate,
                }
            ),
        )

    def link_issue(
        self,
        link_type: str,
        inward_issue: str,
        outward_issue: str,
        *,
        comment: Mapping[str, Any] | None = None,
    ) -> Any:
        return self._execute(
            "Issue bağlantısı oluşturma",
            self.client.create_issue_link,
            link_type,
            inward_issue,
            outward_issue,
            comment=comment,
        )

    def remote_links(self, issue_key: str) -> Sequence[Any]:
        return self._execute(
            "Uzak bağlantıların listelenmesi",
            self.client.remote_links,
            issue_key,
        )

    def add_remote_link(
        self,
        issue_key: str,
        url: str,
        title: str,
        *,
        global_id: str | None = None,
        relationship: str | None = None,
    ) -> Any:
        destination = {"url": url, "title": title}
        return self._execute(
            "Uzak bağlantı ekleme",
            self.client.add_remote_link,
            issue_key,
            destination,
            **_without_none(
                {"globalId": global_id, "relationship": relationship}
            ),
        )

    # Watchers and votes
    def watchers(self, issue_key: str) -> Any:
        return self._execute(
            "Takipçilerin listelenmesi",
            self.client.watchers,
            issue_key,
        )

    def add_watcher(self, issue_key: str, watcher: str) -> Any:
        return self._execute(
            "Takipçi ekleme",
            self.client.add_watcher,
            issue_key,
            watcher,
        )

    def remove_watcher(self, issue_key: str, watcher: str) -> Any:
        return self._execute(
            "Takipçi kaldırma",
            self.client.remove_watcher,
            issue_key,
            watcher,
        )

    def add_vote(self, issue_key: str) -> Any:
        return self._execute("Oy ekleme", self.client.add_vote, issue_key)

    def remove_vote(self, issue_key: str) -> Any:
        return self._execute("Oy kaldırma", self.client.remove_vote, issue_key)

    # Jira Software / Agile
    def boards(
        self,
        *,
        start_at: int = 0,
        max_results: int = 50,
        board_type: str | None = None,
        name: str | None = None,
        project_key: str | None = None,
    ) -> Sequence[Any]:
        return self._execute(
            "Board'ların listelenmesi",
            self.client.boards,
            startAt=start_at,
            maxResults=max_results,
            type=board_type,
            name=name,
            projectKeyOrID=project_key,
        )

    def sprints(
        self,
        board_id: int,
        *,
        start_at: int = 0,
        max_results: int = 50,
        state: str | None = None,
    ) -> Sequence[Any]:
        return self._execute(
            "Sprintlerin listelenmesi",
            self.client.sprints,
            board_id,
            extended=True,
            startAt=start_at,
            maxResults=max_results,
            state=state,
        )

    def sprint(self, sprint_id: int) -> Any:
        return self._execute("Sprint alınması", self.client.sprint, sprint_id)

    def create_sprint(
        self,
        name: str,
        board_id: int,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        goal: str | None = None,
    ) -> Any:
        return self._execute(
            "Sprint oluşturma",
            self.client.create_sprint,
            name,
            board_id,
            **_without_none(
                {
                    "startDate": start_date,
                    "endDate": end_date,
                    "goal": goal,
                }
            ),
        )

    def update_sprint(
        self,
        sprint_id: int,
        *,
        name: str | None = None,
        state: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        goal: str | None = None,
    ) -> Any:
        return self._execute(
            "Sprint güncelleme",
            self.client.update_sprint,
            sprint_id,
            **_without_none(
                {
                    "name": name,
                    "state": state,
                    "startDate": start_date,
                    "endDate": end_date,
                    "goal": goal,
                }
            ),
        )

    def add_issues_to_sprint(
        self,
        sprint_id: int,
        issue_keys: Sequence[str],
    ) -> Any:
        return self._execute(
            "Issue'ları sprinte ekleme",
            self.client.add_issues_to_sprint,
            sprint_id,
            list(issue_keys),
        )

    def move_to_backlog(self, issue_keys: Sequence[str]) -> Any:
        return self._execute(
            "Issue'ları backlog'a taşıma",
            self.client.move_to_backlog,
            list(issue_keys),
        )


def _without_none(values: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in values.items() if value is not None}


_MAX_ERROR_DETAIL_LENGTH = 2_000
_JSON_ERROR_KEYS = ("message", "errorMessage", "errorMessages", "errors", "detail")


def _extract_error_details(exc: Exception, response: Any) -> list[str]:
    """Extract useful Jira errors from JSON, text, HTML and auth headers."""
    details: list[str] = []
    headers = getattr(response, "headers", None)
    if isinstance(headers, Mapping):
        auth_reason = headers.get("x-authentication-denied-reason") or headers.get(
            "X-Authentication-Denied-Reason"
        )
        _append_detail(details, auth_reason)

    payload = _response_json(response)
    if payload is not None:
        _collect_json_errors(payload, details)

    response_body = getattr(response, "text", None)
    if not details and isinstance(response_body, str):
        _append_detail(details, _humanize_response_text(response_body))

    exception_text = getattr(exc, "text", None)
    if not details and isinstance(exception_text, str):
        parsed = _parse_json_text(exception_text)
        if parsed is not None:
            _collect_json_errors(parsed, details)
        else:
            _append_detail(details, _humanize_response_text(exception_text))

    if not details:
        _append_detail(details, str(exc))
    return details


def _response_json(response: Any) -> Any | None:
    if response is None:
        return None
    json_method = getattr(response, "json", None)
    if callable(json_method):
        try:
            return json_method()
        except (TypeError, ValueError, json.JSONDecodeError):
            pass
        except Exception:
            # Error parsing must never hide the original Jira exception.
            pass
    text = getattr(response, "text", None)
    return _parse_json_text(text) if isinstance(text, str) else None


def _parse_json_text(text: str) -> Any | None:
    stripped = text.strip()
    if not stripped or stripped[0] not in "[{":
        return None
    try:
        return json.loads(stripped)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None


def _collect_json_errors(payload: Any, details: list[str]) -> None:
    if isinstance(payload, Mapping):
        matched = False
        for key in _JSON_ERROR_KEYS:
            if key in payload and payload[key] not in (None, "", [], {}):
                matched = True
                _collect_error_value(payload[key], details, include_mapping_keys=key == "errors")
        if not matched:
            # Non-standard Jira proxies sometimes return {"error": "..."}.
            for key in ("error", "title", "reason"):
                if key in payload:
                    _collect_error_value(payload[key], details)
    elif isinstance(payload, (list, tuple)):
        _collect_error_value(payload, details)
    elif isinstance(payload, str):
        _append_detail(details, payload)


def _collect_error_value(
    value: Any,
    details: list[str],
    *,
    include_mapping_keys: bool = False,
) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            before = len(details)
            _collect_error_value(nested, details)
            if include_mapping_keys and len(details) > before:
                details[-1] = f"{key}: {details[-1]}"
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            _collect_error_value(item, details)
    elif value is not None:
        _append_detail(details, str(value))


def _humanize_response_text(text: str) -> str:
    stripped = text.strip()
    if not stripped:
        return ""
    if re.search(r"<(?:!doctype|html|head|body|title)\b", stripped, re.IGNORECASE):
        parser = _ErrorHTMLParser()
        try:
            parser.feed(stripped)
            humanized = parser.message()
            if humanized:
                return humanized
        except Exception:
            pass
        stripped = re.sub(r"<[^>]+>", " ", stripped)
    return _clean_detail(stripped)


def _append_detail(details: list[str], value: Any) -> None:
    if value is None:
        return
    detail = _clean_detail(str(value))
    if detail and detail not in details:
        details.append(detail)


def _clean_detail(value: str) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    if len(value) > _MAX_ERROR_DETAIL_LENGTH:
        return value[: _MAX_ERROR_DETAIL_LENGTH - 1].rstrip() + "…"
    return value


def _first_value(*values: Any) -> Any | None:
    for value in values:
        if isinstance(value, (str, int)) and value != "":
            return value
    return None


class _ErrorHTMLParser(HTMLParser):
    """Small dependency-free extractor for reverse-proxy and Jira HTML errors."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._title: list[str] = []
        self._body: list[str] = []
        self._in_title = False
        self._in_body = False
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript"}:
            self._ignored_depth += 1
        elif tag == "title":
            self._in_title = True
        elif tag == "body":
            self._in_body = True

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript"} and self._ignored_depth:
            self._ignored_depth -= 1
        elif tag == "title":
            self._in_title = False
        elif tag == "body":
            self._in_body = False

    def handle_data(self, data: str) -> None:
        if self._ignored_depth:
            return
        if self._in_title:
            self._title.append(data)
        elif self._in_body:
            self._body.append(data)

    def message(self) -> str:
        title = _clean_detail(" ".join(self._title))
        body = _clean_detail(" ".join(self._body))
        if title and body and title.lower() not in body.lower():
            return f"{title}: {body}"
        return body or title
