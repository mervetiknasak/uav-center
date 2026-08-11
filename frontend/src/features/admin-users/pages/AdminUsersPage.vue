<script setup>
import { onMounted } from "vue";

import { useAppContext } from "../../../app/bootstrap";
import { useAdminUsers } from "../../../composables/useAdminUsers";
import AdminMembershipView from "../../../views/AdminMembershipView.vue";

const { api, auth } = useAppContext();
const adminUsers = useAdminUsers(api.apiFetch);

onMounted(() => adminUsers.loadUsersIfAdmin(auth.currentUser.value));
</script>

<template>
  <AdminMembershipView
    :users="adminUsers.users.value"
    :loading="adminUsers.loading.value"
    :error="adminUsers.error.value"
    :updating-user-id="adminUsers.updatingUserId.value"
    @refresh="adminUsers.loadUsers"
    @update-status="adminUsers.updateUserStatus"
  />
</template>
