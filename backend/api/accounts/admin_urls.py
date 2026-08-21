from django.urls import path

from .views import AdminUserEDKRolesView, AdminUserListView, AdminUserStatusView

urlpatterns = [
    path("", AdminUserListView.as_view(), name="admin-user-list"),
    path("<int:user_id>/status/", AdminUserStatusView.as_view(), name="admin-user-status"),
    path(
        "<int:user_id>/edk-roles/",
        AdminUserEDKRolesView.as_view(),
        name="admin-user-edk-roles",
    ),
]
