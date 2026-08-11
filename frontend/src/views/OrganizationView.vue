<script setup>
import OrganizationScreen from "../features/organization/components/OrganizationScreen.vue";

defineProps({
  projects: { type: Array, required: true },
  personGroups: { type: Array, default: () => [] },
  loading: { type: Boolean, required: true },
  saving: { type: Boolean, required: true },
  error: { type: String, default: "" },
  canEdit: { type: Boolean, default: false }
});

const emit = defineEmits(["refresh", "save", "delete", "reorder-responsibles"]);
</script>

<template>
  <OrganizationScreen
    v-bind="$props"
    @refresh="emit('refresh')"
    @save="emit('save', $event)"
    @delete="emit('delete', $event)"
    @reorder-responsibles="emit('reorder-responsibles', $event)"
  />
</template>
