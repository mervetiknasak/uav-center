from django.urls import path

from .views import (
    EDKApplicationDecisionView,
    EDKApplicationDetailView,
    EDKApplicationJiraPublishView,
    EDKApplicationJiraRefreshView,
    EDKApplicationListCreateView,
    EDKApplicationPresentationView,
    EDKJiraPublishView,
    EDKMeetingMinutesParseView,
)

urlpatterns = [
    path("applications/", EDKApplicationListCreateView.as_view(), name="edk-application-list"),
    path(
        "applications/<int:application_id>/",
        EDKApplicationDetailView.as_view(),
        name="edk-application-detail",
    ),
    path(
        "applications/<int:application_id>/decision/",
        EDKApplicationDecisionView.as_view(),
        name="edk-application-decision",
    ),
    path(
        "applications/<int:application_id>/presentation/",
        EDKApplicationPresentationView.as_view(),
        name="edk-application-presentation",
    ),
    path(
        "applications/<int:application_id>/minutes/parse/",
        EDKMeetingMinutesParseView.as_view(),
        name="edk-minutes-parse",
    ),
    path(
        "applications/<int:application_id>/jira/publish/",
        EDKApplicationJiraPublishView.as_view(),
        name="edk-application-jira-publish",
    ),
    path(
        "applications/<int:application_id>/jira/refresh/",
        EDKApplicationJiraRefreshView.as_view(),
        name="edk-application-jira-refresh",
    ),
    path("jira/publish/", EDKJiraPublishView.as_view(), name="edk-jira-publish"),
]
