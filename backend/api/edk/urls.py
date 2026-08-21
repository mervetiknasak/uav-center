from django.urls import path

from .views import (
    EDKApplicationDecisionView,
    EDKApplicationListCreateView,
    EDKJiraPublishView,
    EDKMeetingMinutesParseView,
)

urlpatterns = [
    path("applications/", EDKApplicationListCreateView.as_view(), name="edk-application-list"),
    path(
        "applications/<int:application_id>/decision/",
        EDKApplicationDecisionView.as_view(),
        name="edk-application-decision",
    ),
    path(
        "applications/<int:application_id>/minutes/parse/",
        EDKMeetingMinutesParseView.as_view(),
        name="edk-minutes-parse",
    ),
    path("jira/publish/", EDKJiraPublishView.as_view(), name="edk-jira-publish"),
]
