from rest_framework.permissions import IsAdminUser, IsAuthenticated


class IsActiveAuthenticated(IsAuthenticated):
    """Require both an authenticated session and an active account."""

    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_active


class IsActiveAdminUser(IsAdminUser):
    """Require an active staff account."""

    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_active
