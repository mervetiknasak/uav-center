import { ref } from "vue";
import { errorMessage } from "./errorMessage";

export function useAdminUsers(apiFetch) {
  const users = ref([]);
  const loading = ref(false);
  const error = ref("");
  const updatingUserId = ref(null);

  async function loadUsers() {
    loading.value = true;
    error.value = "";
    try {
      const data = await apiFetch("/api/admin/users/");
      users.value = Array.isArray(data) ? data : [];
    } catch (err) {
      error.value = errorMessage(err, "Üyeler alınamadı");
    } finally {
      loading.value = false;
    }
  }

  async function loadUsersIfAdmin(user) {
    if (user?.is_staff) await loadUsers();
  }

  async function updateUserStatus(user, isActive) {
    updatingUserId.value = user.id;
    error.value = "";
    try {
      const updatedUser = await apiFetch(`/api/admin/users/${user.id}/status/`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ is_active: isActive })
      });
      users.value = users.value.map((item) => (item.id === updatedUser.id ? updatedUser : item));
    } catch (err) {
      error.value = errorMessage(err, "Kullanıcı durumu güncellenemedi");
    } finally {
      updatingUserId.value = null;
    }
  }

  async function updateUserEDKRoles(user, edkRoles) {
    updatingUserId.value = user.id;
    error.value = "";
    try {
      const updatedUser = await apiFetch(`/api/admin/users/${user.id}/edk-roles/`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ edk_roles: edkRoles })
      });
      users.value = users.value.map((item) => (item.id === updatedUser.id ? updatedUser : item));
    } catch (err) {
      error.value = errorMessage(err, "EDK rolleri güncellenemedi");
    } finally {
      updatingUserId.value = null;
    }
  }

  function resetUsers() {
    users.value = [];
    error.value = "";
    updatingUserId.value = null;
  }

  return {
    users,
    loading,
    error,
    updatingUserId,
    loadUsers,
    loadUsersIfAdmin,
    updateUserStatus,
    updateUserEDKRoles,
    resetUsers
  };
}
