from django.contrib.auth.models import Group

EDK_ROLE_APPLICANT = "applicant"
EDK_ROLE_APPROVER = "approver"

EDK_ROLE_GROUPS = {
    EDK_ROLE_APPLICANT: "EDK Başvuru Sahibi",
    EDK_ROLE_APPROVER: "EDK Onaylayıcı",
}


def edk_roles_for_user(user):
    if not user or not user.is_authenticated or not user.is_active:
        return []
    if user.is_superuser:
        return list(EDK_ROLE_GROUPS)
    group_names = {group.name for group in user.groups.all()}
    return [role for role, group_name in EDK_ROLE_GROUPS.items() if group_name in group_names]


def user_has_edk_role(user, role):
    return role in edk_roles_for_user(user)


def replace_edk_roles(user, roles):
    managed_groups = {
        role: Group.objects.get_or_create(name=group_name)[0]
        for role, group_name in EDK_ROLE_GROUPS.items()
    }
    user.groups.remove(*managed_groups.values())
    user.groups.add(*(managed_groups[role] for role in roles))


def ensure_default_edk_role(user):
    if not edk_roles_for_user(user):
        default_role = EDK_ROLE_APPROVER if user.is_staff else EDK_ROLE_APPLICANT
        replace_edk_roles(user, [default_role])
