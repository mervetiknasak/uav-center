"""Architecture characterization tests for stable API compatibility seams."""

import ast
from collections import Counter
from pathlib import Path

from django.test import SimpleTestCase
from django.urls.resolvers import URLPattern, URLResolver

from . import models as model_facade
from . import serializers as serializer_facade
from . import views as view_facade
from .urls import urlpatterns

EXPECTED_MODEL_EXPORTS = {
    "AnalysisControl",
    "AsyncJob",
    "CoverPage",
    "Document",
    "DocumentAnalysisRun",
    "DocumentChunk",
    "FlightPermit",
    "PanelResponsible",
    "Person",
    "PersonGroup",
    "Project",
    "ProjectPanel",
    "TechnicalDocument",
    "TechnicalDocumentNotification",
    "TechnicalDocumentStatusHistory",
}

EXPECTED_SERIALIZER_EXPORTS = {
    "AdminUserSerializer",
    "AdminUserStatusSerializer",
    "AnalysisControlSerializer",
    "AsyncJobSerializer",
    "CoverPageSerializer",
    "DocumentAnalysisRunSerializer",
    "DocumentControlRunSerializer",
    "DocumentDetailSerializer",
    "DocumentListSerializer",
    "DocumentRagQuerySerializer",
    "DocumentUploadSerializer",
    "FlightPermitSerializer",
    "LoginSerializer",
    "OllamaChatMessageSerializer",
    "OllamaChatRequestSerializer",
    "PanelResponsibleSerializer",
    "PersonGroupSerializer",
    "PersonSerializer",
    "ProjectPanelSerializer",
    "ProjectSerializer",
    "RegisterSerializer",
    "TechnicalDocumentNotificationRequestSerializer",
    "TechnicalDocumentNotificationSerializer",
    "TechnicalDocumentPanelSerializer",
    "TechnicalDocumentSerializer",
    "TechnicalDocumentStatusHistorySerializer",
    "UserSerializer",
    "WordToJiraPublishRequestSerializer",
}

EXPECTED_VIEW_EXPORTS = {
    "AdminUserListView",
    "AdminUserStatusView",
    "AnalysisControlDetailView",
    "AnalysisControlListCreateView",
    "AsyncJobCancelView",
    "AsyncJobDetailView",
    "AsyncJobListView",
    "CsrfTokenView",
    "CurrentUserView",
    "DocumentAnalysisRunListView",
    "DocumentControlRunView",
    "DocumentDetailView",
    "DocumentListView",
    "DocumentRagQueryView",
    "DocumentUploadView",
    "FlightPermitDetailView",
    "FlightPermitDocumentView",
    "FlightPermitGeneratedDocumentView",
    "FlightPermitListCreateView",
    "GroupPersonListCreateView",
    "IsActiveAdminUser",
    "IsActiveAuthenticated",
    "IsOrganizationReaderOrAdmin",
    "LoginView",
    "LogoutView",
    "OllamaChatView",
    "OllamaPullView",
    "OllamaStatusView",
    "OllamaUnloadView",
    "PanelResponsibleDetailView",
    "PanelResponsibleListCreateView",
    "PersonDetailView",
    "PersonGroupDetailView",
    "PersonGroupListCreateView",
    "ProjectDetailView",
    "ProjectListCreateView",
    "ProjectPanelDetailView",
    "ProjectPanelListCreateView",
    "RegisterView",
    "TechnicalDocumentDetailView",
    "TechnicalDocumentListCreateView",
    "TechnicalDocumentNotifyView",
    "WordTableParseView",
    "WordToJiraPublishView",
    "health_check",
    "process_document_text",
    "readiness_check",
    "technical_document_queryset",
}

EXPECTED_NAMED_ROUTES = {
    "health-check": "health/",
    "health-ready": "health/ready/",
    "csrf-token": "auth/csrf/",
    "current-user": "auth/me/",
    "login": "auth/login/",
    "logout": "auth/logout/",
    "register": "auth/register/",
    "admin-user-list": "admin/users/",
    "admin-user-status": "admin/users/<int:user_id>/status/",
    "project-list": "organization/projects/",
    "project-detail": "organization/projects/<int:project_id>/",
    "project-panel-list": "organization/projects/<int:project_id>/panels/",
    "project-panel-detail": "organization/panels/<int:panel_id>/",
    "panel-responsible-list": "organization/panels/<int:panel_id>/responsibles/",
    "panel-responsible-detail": "organization/responsibles/<int:responsible_id>/",
    "person-group-list": "organization/person-groups/",
    "person-group-detail": "organization/person-groups/<int:group_id>/",
    "group-person-list": "organization/person-groups/<int:group_id>/people/",
    "person-detail": "organization/people/<int:person_id>/",
    "document-list": "documents/",
    "document-upload": "documents/upload/",
    "document-detail": "documents/<int:document_id>/",
    "document-rag-query": "documents/<int:document_id>/rag/query/",
    "document-analysis-runs": "documents/<int:document_id>/analyses/",
    "document-control-run": "documents/<int:document_id>/controls/run/",
    "analysis-control-list": "analysis-controls/",
    "analysis-control-detail": "analysis-controls/<int:control_id>/",
    "job-list": "jobs/",
    "job-detail": "jobs/<uuid:job_id>/",
    "job-cancel": "jobs/<uuid:job_id>/cancel/",
    "ollama-status": "ai/ollama/status/",
    "ollama-pull": "ai/ollama/pull/",
    "ollama-unload": "ai/ollama/unload/",
    "ollama-chat": "ai/ollama/chat/",
    "flight-permit-list": "flight-permits/",
    "flight-permit-detail": "flight-permits/<int:flight_permit_id>/",
    "flight-permit-document": "flight-permits/<int:flight_permit_id>/document/",
    "flight-permit-generated-document": (
        "flight-permits/<int:flight_permit_id>/generated-document/"
    ),
    "technical-document-list": "technical-documents/",
    "technical-document-detail": "technical-documents/<int:technical_document_id>/",
    "technical-document-notify": ("technical-documents/<int:technical_document_id>/notify/"),
    "word-table-parse": "word-to-jira/parse/",
    "word-to-jira-publish": "word-to-jira/publish/",
}

FORBIDDEN_FACADE_MODULES = {"api.models", "api.serializers", "api.views"}


def _named_routes(patterns, prefix=""):
    routes = []
    for pattern in patterns:
        route = f"{prefix}{pattern.pattern}"
        if isinstance(pattern, URLResolver):
            routes.extend(_named_routes(pattern.url_patterns, route))
        elif isinstance(pattern, URLPattern) and pattern.name:
            routes.append((pattern.name, route))
    return routes


def _resolved_from_module(node: ast.ImportFrom, package_parts: list[str]) -> str:
    if not node.level:
        return node.module or ""

    keep = len(package_parts) - (node.level - 1)
    resolved_parts = package_parts[: max(keep, 0)]
    if node.module:
        resolved_parts.extend(node.module.split("."))
    return ".".join(resolved_parts)


def _forbidden_facade_imports(source: str, package_parts: list[str]) -> list[tuple[int, str]]:
    violations = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            violations.extend(
                (node.lineno, alias.name)
                for alias in node.names
                if alias.name in FORBIDDEN_FACADE_MODULES
            )
            continue
        if not isinstance(node, ast.ImportFrom):
            continue

        resolved = _resolved_from_module(node, package_parts)
        if resolved in FORBIDDEN_FACADE_MODULES:
            violations.append((node.lineno, resolved))
        elif resolved == "api":
            violations.extend(
                (node.lineno, candidate)
                for alias in node.names
                if (candidate := f"api.{alias.name}") in FORBIDDEN_FACADE_MODULES
            )
    return violations


class ApiArchitectureTests(SimpleTestCase):
    def test_feature_models_keep_historical_api_app_label(self):
        self.assertEqual(set(model_facade.__all__), EXPECTED_MODEL_EXPORTS)
        for model_name in model_facade.__all__:
            with self.subTest(model=model_name):
                model = getattr(model_facade, model_name)
                self.assertEqual(model._meta.app_label, "api")

    def test_compatibility_facades_have_explicit_characterized_exports(self):
        self.assertEqual(set(serializer_facade.__all__), EXPECTED_SERIALIZER_EXPORTS)
        self.assertEqual(set(view_facade.__all__), EXPECTED_VIEW_EXPORTS)
        for facade in (model_facade, serializer_facade, view_facade):
            for exported_name in facade.__all__:
                with self.subTest(facade=facade.__name__, export=exported_name):
                    self.assertTrue(hasattr(facade, exported_name))

    def test_43_named_routes_remain_unique_and_unchanged(self):
        routes = _named_routes(urlpatterns)
        counts = Counter(name for name, _route in routes)

        self.assertEqual(len(routes), 43)
        self.assertEqual(
            {name for name, count in counts.items() if count > 1},
            set(),
        )
        self.assertEqual(dict(routes), EXPECTED_NAMED_ROUTES)

    def test_facade_import_rule_covers_direct_aliased_and_relative_syntax(self):
        cases = {
            "import api.models": "api.models",
            "from api.models import Document": "api.models",
            "from api import serializers as serializers_facade": "api.serializers",
            "from .. import views": "api.views",
        }
        for source, target in cases.items():
            with self.subTest(source=source):
                self.assertEqual(
                    _forbidden_facade_imports(source, ["api", "documents"]),
                    [(1, target)],
                )

        self.assertEqual(
            _forbidden_facade_imports(
                "from api.documents import models",
                ["api", "documents"],
            ),
            [],
        )

    def test_production_modules_do_not_depend_on_compatibility_facades(self):
        api_root = Path(__file__).parent
        violations = []

        for source_path in api_root.rglob("*.py"):
            relative = source_path.relative_to(api_root)
            if (
                source_path.name in {"models.py", "serializers.py", "views.py"}
                and source_path.parent == api_root
            ):
                continue
            if "migrations" in relative.parts or source_path.name.startswith("test"):
                continue

            module_parts = ["api", *relative.with_suffix("").parts]
            package_parts = module_parts[:-1]
            source = source_path.read_text(encoding="utf-8")
            for line_number, resolved in _forbidden_facade_imports(source, package_parts):
                violations.append(f"{relative}:{line_number} -> {resolved}")

        self.assertEqual(violations, [])
