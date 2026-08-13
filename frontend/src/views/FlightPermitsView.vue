<script setup>
import FlightPermitsScreen from "../features/flight-permits/components/FlightPermitsScreen.vue";

defineProps({
  permits: { type: Array, required: true },
  templates: { type: Array, default: () => [] },
  loading: { type: Boolean, required: true },
  saving: { type: Boolean, required: true },
  error: { type: String, default: "" },
  notice: { type: String, default: "" }
});

const emit = defineEmits(["refresh", "save", "delete"]);
</script>

<template>
  <FlightPermitsScreen
    v-bind="$props"
    @refresh="emit('refresh')"
    @save="emit('save', $event)"
    @delete="emit('delete', $event)"
  />
</template>
