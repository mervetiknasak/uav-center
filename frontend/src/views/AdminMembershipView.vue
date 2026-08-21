<script setup>
import AdminMembershipScreen from "../features/admin-users/components/AdminMembershipScreen.vue";

defineProps({
  users: {
    type: Array,
    required: true
  },
  roleCatalog: {
    type: Array,
    default: undefined
  },
  loading: {
    type: Boolean,
    required: true
  },
  error: {
    type: String,
    default: ""
  },
  updatingUserId: {
    type: Number,
    default: null
  }
});

const emit = defineEmits(["refresh", "update-status", "update-edk-roles"]);

function forwardStatusUpdate(...args) {
  emit("update-status", ...args);
}

function forwardRoleUpdate(...args) {
  emit("update-edk-roles", ...args);
}
</script>

<template>
  <AdminMembershipScreen
    v-bind="$props"
    @refresh="emit('refresh')"
    @update-status="forwardStatusUpdate"
    @update-roles="forwardRoleUpdate"
  />
</template>
