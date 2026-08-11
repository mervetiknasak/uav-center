<script setup>
import { computed, onMounted } from "vue";
import { useRoute } from "vue-router";

import { useAppContext } from "../../../app/bootstrap";
import OrganizationScreen from "../components/OrganizationScreen.vue";
import { useOrganization } from "../composables/useOrganization";

const { api, auth } = useAppContext();
const route = useRoute();
const organization = useOrganization(api.apiFetch);
const canEdit = computed(
  () => route.name === "organization-admin" && Boolean(auth.currentUser.value?.is_staff)
);

onMounted(organization.loadOrganization);
</script>

<template>
  <OrganizationScreen
    :projects="organization.projects.value"
    :person-groups="organization.personGroups.value"
    :loading="organization.loading.value"
    :saving="organization.saving.value"
    :error="organization.error.value"
    :can-edit="canEdit"
    @refresh="organization.loadOrganization"
    @save="organization.saveItem"
    @delete="organization.deleteItem"
    @reorder-responsibles="organization.reorderResponsibles"
  />
</template>
