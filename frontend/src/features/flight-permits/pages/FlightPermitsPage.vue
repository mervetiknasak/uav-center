<script setup>
import { onMounted } from "vue";

import { useAppContext } from "../../../app/bootstrap";
import FlightPermitsScreen from "../components/FlightPermitsScreen.vue";
import { useFlightPermits } from "../composables/useFlightPermits";

const { api } = useAppContext();
const flightPermits = useFlightPermits(api.apiFetch);

onMounted(flightPermits.loadPermits);
</script>

<template>
  <FlightPermitsScreen
    :permits="flightPermits.permits.value"
    :loading="flightPermits.loading.value"
    :saving="flightPermits.saving.value"
    :error="flightPermits.error.value"
    :notice="flightPermits.notice.value"
    @refresh="flightPermits.loadPermits"
    @save="flightPermits.savePermit"
    @delete="flightPermits.deletePermit"
  />
</template>
