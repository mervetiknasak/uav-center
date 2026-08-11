from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsOrganizationReaderOrAdmin(BasePermission):
    """Active users may read organization data; only staff may mutate it."""

    def has_permission(self, request, view):
        if not request.user.is_authenticated or not request.user.is_active:
            return False
        return request.method in SAFE_METHODS or request.user.is_staff
