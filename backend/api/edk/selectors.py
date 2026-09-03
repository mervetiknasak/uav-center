from .models import EDKApplication
from .roles import EDK_ROLE_APPROVER, user_has_edk_role


def edk_applications_visible_to(user):
    queryset = EDKApplication.objects.select_related("applicant", "project", "reviewed_by")
    if user_has_edk_role(user, EDK_ROLE_APPROVER):
        return queryset
    return queryset.filter(applicant=user)


def edk_applications_publishable_to_jira_by(user):
    queryset = EDKApplication.objects.all()
    if user.is_staff:
        return queryset
    return queryset.filter(applicant=user)
