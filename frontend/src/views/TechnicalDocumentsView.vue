<script setup>
import TechnicalDocumentsScreen from "../features/technical-documents/components/TechnicalDocumentsScreen.vue";

defineProps({
  projects: { type: Array, required: true },
  documents: { type: Array, required: true },
  loading: { type: Boolean, required: true },
  saving: { type: Boolean, required: true },
  notifyingId: { type: Number, default: null },
  error: { type: String, default: "" },
  notice: { type: String, default: "" },
  canEdit: { type: Boolean, default: false }
});

const emit = defineEmits(["refresh", "save", "delete", "notify"]);
</script>

<template>
  <TechnicalDocumentsScreen
    v-bind="$props"
    @refresh="emit('refresh')"
    @save="emit('save', $event)"
    @delete="emit('delete', $event)"
    @notify="emit('notify', $event)"
  />
</template>
