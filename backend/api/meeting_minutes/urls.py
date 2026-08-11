from django.urls import path

from .views import WordTableParseView, WordToJiraPublishView

urlpatterns = [
    path("parse/", WordTableParseView.as_view(), name="word-table-parse"),
    path("publish/", WordToJiraPublishView.as_view(), name="word-to-jira-publish"),
]
