<script setup>
import { computed, onMounted } from "vue";

import { useAppContext } from "../../../app/bootstrap";
import EDKScreen from "../components/EDKScreen.vue";
import { useEdk } from "../composables/useEdk";

const { api, auth } = useAppContext();
const edk = useEdk(api.apiFetch);
const canPublish = computed(() => Boolean(auth.currentUser.value?.is_staff));
const edkRoles = computed(() => auth.currentUser.value?.edk_roles || []);

onMounted(() => {
  if (edkRoles.value.length) edk.loadApplications();
});

async function createApplication({ application, onSuccess }) {
  if (await edk.createApplication(application)) onSuccess();
}

function publish(draft) {
  if (!canPublish.value) return;
  edk.publish(draft);
}
</script>

<template>
  <EDKScreen
    :loading="edk.parseLoading.value"
    :applications="edk.applications.value"
    :applications-loading="edk.applicationsLoading.value"
    :application-submitting="edk.applicationSubmitting.value"
    :decision-loading-id="edk.decisionLoadingId.value"
    :edk-roles="edkRoles"
    :current-user-name="auth.currentUser.value?.username || ''"
    :publishing="edk.publishLoading.value"
    :error="edk.error.value"
    :result="edk.parseResult.value"
    :publish-result="edk.publishResult.value"
    :can-publish="canPublish"
    @parse="edk.parse"
    @create-application="createApplication"
    @decide="edk.decide"
    @publish="publish"
  />
</template>
