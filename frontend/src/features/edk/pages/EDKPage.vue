<script setup>
import { computed, onMounted } from "vue";
import { useRouter } from "vue-router";

import { useAppContext } from "../../../app/bootstrap";
import EDKScreen from "../components/EDKScreen.vue";
import { useEdk } from "../composables/useEdk";

const { api, auth } = useAppContext();
const router = useRouter();
const edk = useEdk(api.apiFetch);
const edkRoles = computed(() => auth.currentUser.value?.edk_roles || []);

onMounted(() => {
  if (edkRoles.value.length) edk.loadApplications();
});

async function createApplication({ application, onSuccess }) {
  if (await edk.createApplication(application)) onSuccess();
}

function selectApplication(application) {
  router.push({ name: "edk-application-detail", params: { applicationId: application.id } });
}
</script>

<template>
  <EDKScreen
    :applications="edk.applications.value"
    :applications-loading="edk.applicationsLoading.value"
    :application-submitting="edk.applicationSubmitting.value"
    :edk-roles="edkRoles"
    :error="edk.error.value"
    @create-application="createApplication"
    @select-application="selectApplication"
  />
</template>
