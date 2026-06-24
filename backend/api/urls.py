from django.urls import path

from .views import (
    CsrfTokenView,
    CurrentUserView,
    DocumentDetailView,
    DocumentListView,
    DocumentUploadView,
    LoginView,
    LogoutView,
    RegisterView,
    health_check,
)

urlpatterns = [
    path("health/", health_check, name="health-check"),
    path("auth/csrf/", CsrfTokenView.as_view(), name="csrf-token"),
    path("auth/me/", CurrentUserView.as_view(), name="current-user"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("documents/", DocumentListView.as_view(), name="document-list"),
    path("documents/upload/", DocumentUploadView.as_view(), name="document-upload"),
    path("documents/<int:document_id>/", DocumentDetailView.as_view(), name="document-detail"),
]
