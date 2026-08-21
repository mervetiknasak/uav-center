from django.urls import path

from .views import OperationalAlertListView

urlpatterns = [
    path("", OperationalAlertListView.as_view(), name="operational-alert-list"),
]
