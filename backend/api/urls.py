"""API URL composition for feature-owned route modules."""

from django.urls import include, path

from .common.readiness import readiness_check
from .common.views import health_check

urlpatterns = [
    path("health/", health_check, name="health-check"),
    path("health/ready/", readiness_check, name="health-ready"),
    path("auth/", include("api.accounts.auth_urls")),
    path("admin/users/", include("api.accounts.admin_urls")),
    path("organization/", include("api.organization.urls")),
    path("documents/", include("api.documents.urls")),
    path("analysis-controls/", include("api.documents.control_urls")),
    path("jobs/", include("api.jobs.urls")),
    path("ai/ollama/", include("api.ai.urls")),
    path("flight-permits/", include("api.flight_permits.urls")),
    path("form-processes/", include("api.form_processes.urls")),
    path("technical-documents/", include("api.technical_documents.urls")),
    path("word-to-jira/", include("api.meeting_minutes.urls")),
]
