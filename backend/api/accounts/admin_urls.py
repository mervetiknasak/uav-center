from django.urls import path

from .views import AdminUserListView, AdminUserStatusView

urlpatterns = [
    path("", AdminUserListView.as_view(), name="admin-user-list"),
    path("<int:user_id>/status/", AdminUserStatusView.as_view(), name="admin-user-status"),
]
