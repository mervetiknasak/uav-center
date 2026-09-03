<script setup>
import { computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";

import { useAppContext } from "../../../app/bootstrap";
import EDKApplicationDetailScreen from "../components/EDKApplicationDetailScreen.vue";
import { useEdkApplicationDetail } from "../composables/useEdkApplicationDetail";

const route = useRoute();
const router = useRouter();
const { api, auth } = useAppContext();
const detail = useEdkApplicationDetail(api.apiFetch);
const applicationId = computed(() => Number(route.params.applicationId));
const canPublish = computed(() => Boolean(auth.currentUser.value?.is_staff));
const edkRoles = computed(() => auth.currentUser.value?.edk_roles || []);

onMounted(() => detail.loadApplication(applicationId.value));

function goBack() {
  router.push({ name: "edk" });
}

function publish(draft) {
  if (canPublish.value) detail.publish(draft);
}
</script>

<template>
  <EDKApplicationDetailScreen
    :application="detail.application.value"
    :loading="detail.loading.value"
    :decision-loading="detail.decisionLoading.value"
    :parse-loading="detail.parseLoading.value"
    :publishing="detail.publishLoading.value"
    :tracking-loading="detail.trackingLoading.value"
    :edk-roles="edkRoles"
    :current-user-name="auth.currentUser.value?.username || ''"
    :error="detail.error.value"
    :result="detail.parseResult.value"
    :publish-result="detail.publishResult.value"
    :can-publish="canPublish"
    @back="goBack"
    @decide="detail.decide"
    @parse="detail.parse"
    @publish="publish"
    @refresh-jira="detail.refreshJiraTracking"
  />
</template>
