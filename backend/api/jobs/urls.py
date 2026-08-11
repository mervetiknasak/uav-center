from django.urls import path

from .views import AsyncJobCancelView, AsyncJobDetailView, AsyncJobListView

urlpatterns = [
    path("", AsyncJobListView.as_view(), name="job-list"),
    path("<uuid:job_id>/", AsyncJobDetailView.as_view(), name="job-detail"),
    path("<uuid:job_id>/cancel/", AsyncJobCancelView.as_view(), name="job-cancel"),
]
