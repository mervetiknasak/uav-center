export const DEFAULT_ROLE_CATALOG = [
  {
    id: "applicant",
    name: "Başvuru sahibi",
    title: "Başvuru oluşturur",
    description: "Kendi EDK başvurularını hazırlar, takip eder ve onay sonrası tutanak yükler.",
    category: {
      id: "edk",
      label: "EDK Süreci",
      description: "EDK başvurularının hazırlanması ve değerlendirilmesi"
    }
  },
  {
    id: "approver",
    name: "Onaylayıcı",
    title: "Başvuruları değerlendirir",
    description: "Tüm EDK başvurularını görür; kendi başvurusu hariç onay veya ret kararı verir.",
    category: {
      id: "edk",
      label: "EDK Süreci",
      description: "EDK başvurularının hazırlanması ve değerlendirilmesi"
    }
  }
];

export const MEMBERSHIP_STATUS_OPTIONS = [
  { label: "Tüm durumlar", value: "all" },
  { label: "Aktif kullanıcılar", value: "active" },
  { label: "Pasif kullanıcılar", value: "inactive" }
];

export function assignedRoleIds(user) {
  if (Array.isArray(user?.roles)) return user.roles;
  return Array.isArray(user?.edk_roles) ? user.edk_roles : [];
}

export function membershipRoleOptions(roleCatalog = DEFAULT_ROLE_CATALOG) {
  return [
    { label: "Tüm roller", value: "all" },
    { label: "Rol atanmış", value: "assigned" },
    { label: "Rol atanmamış", value: "unassigned" },
    ...roleCatalog.map((role) => ({ label: role.name, value: role.id }))
  ];
}

export function updateRoleSelection(
  currentRoleIds,
  roleId,
  enabled,
  roleCatalog = DEFAULT_ROLE_CATALOG
) {
  const roleIds = new Set(currentRoleIds);
  if (enabled) roleIds.add(roleId);
  else roleIds.delete(roleId);

  const catalogOrder = roleCatalog.map((role) => role.id);
  const knownRoles = catalogOrder.filter((id) => roleIds.has(id));
  const unknownRoles = [...roleIds].filter((id) => !catalogOrder.includes(id));
  return [...knownRoles, ...unknownRoles];
}

export function rolesForUser(user, roleCatalog = DEFAULT_ROLE_CATALOG) {
  const assignedIds = new Set(assignedRoleIds(user));
  return roleCatalog.filter((role) => assignedIds.has(role.id));
}

export function filterMembershipUsers(
  users,
  { query = "", status = "all", role = "all" },
  roleCatalog = DEFAULT_ROLE_CATALOG
) {
  const normalizedQuery = query.trim().toLocaleLowerCase("tr-TR");
  const catalogRoleIds = new Set(roleCatalog.map((item) => item.id));

  return users.filter((user) => {
    const roles = assignedRoleIds(user).filter((id) => catalogRoleIds.has(id));
    const matchesQuery =
      !normalizedQuery ||
      [user.username, user.email]
        .filter(Boolean)
        .some((value) => value.toLocaleLowerCase("tr-TR").includes(normalizedQuery));
    const matchesStatus =
      status === "all" ||
      (status === "active" && user.is_active) ||
      (status === "inactive" && !user.is_active);
    const matchesRole =
      role === "all" ||
      (role === "assigned" && roles.length > 0) ||
      (role === "unassigned" && roles.length === 0) ||
      roles.includes(role);

    return matchesQuery && matchesStatus && matchesRole;
  });
}

export function filterRoleCatalog(roleCatalog, query = "") {
  const normalizedQuery = query.trim().toLocaleLowerCase("tr-TR");
  if (!normalizedQuery) return roleCatalog;

  return roleCatalog.filter((role) =>
    [role.name, role.title, role.description, role.category?.label]
      .filter(Boolean)
      .some((value) => value.toLocaleLowerCase("tr-TR").includes(normalizedQuery))
  );
}

export function groupRoleCatalog(roleCatalog) {
  const groups = new Map();
  roleCatalog.forEach((role) => {
    const category = role.category || { id: "other", label: "Diğer Roller", description: "" };
    if (!groups.has(category.id)) groups.set(category.id, { ...category, roles: [] });
    groups.get(category.id).roles.push(role);
  });
  return [...groups.values()];
}

export function sameRoleSelection(left, right) {
  if (left.length !== right.length) return false;
  const rightIds = new Set(right);
  return left.every((roleId) => rightIds.has(roleId));
}

export function userInitials(username = "") {
  const words = username
    .trim()
    .split(/[\s._-]+/)
    .filter(Boolean);
  return words
    .slice(0, 2)
    .map((word) => word.charAt(0).toLocaleUpperCase("tr-TR"))
    .join("");
}
