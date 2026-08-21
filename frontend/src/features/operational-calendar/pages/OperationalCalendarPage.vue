<script setup>
import { onMounted } from "vue";
import { useRouter } from "vue-router";

import { useAppContext } from "../../../app/bootstrap";
import OperationalCalendarScreen from "../components/OperationalCalendarScreen.vue";
import { useOperationalAlerts } from "../composables/useOperationalAlerts";
import { operationalAlertRoute } from "../model/alerts";

const { api } = useAppContext();
const router = useRouter();
const operationalAlerts = useOperationalAlerts(api.apiFetch);

function navigateToAlert(alert, action = "open") {
  return router.push(operationalAlertRoute(alert, action));
}

onMounted(operationalAlerts.loadAlerts);
</script>

<template>
  <OperationalCalendarScreen
    :data="operationalAlerts.data.value"
    :loading="operationalAlerts.loading.value"
    :error="operationalAlerts.error.value"
    @refresh="operationalAlerts.loadAlerts"
    @open="navigateToAlert"
    @notify="navigateToAlert($event, 'notify')"
  />
</template>
