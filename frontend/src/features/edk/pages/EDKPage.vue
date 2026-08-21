<script setup>
import { computed, onMounted } from "vue";
import { useRouter } from "vue-router";

import { useAppContext } from "../../../app/bootstrap";
import { useOrganizationProjects } from "../../../composables/useOrganizationProjects";
import EDKScreen from "../components/EDKScreen.vue";
import { useEdk } from "../composables/useEdk";

const { api, auth } = useAppContext();
const router = useRouter();
const edk = useEdk(api.apiFetch);
const projectDirectory = useOrganizationProjects(api.apiFetch);
const edkRoles = computed(() => auth.currentUser.value?.edk_roles || []);
const pageError = computed(() => edk.error.value || projectDirectory.error.value);

onMounted(() => {
  if (edkRoles.value.length) {
    edk.loadApplications();
    if (edkRoles.value.includes("applicant")) projectDirectory.loadProjects();
  }
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
    :projects="projectDirectory.projects.value"
    :projects-loading="projectDirectory.loading.value"
    :edk-roles="edkRoles"
    :error="pageError"
    @create-application="createApplication"
    @select-application="selectApplication"
  />
</template>
