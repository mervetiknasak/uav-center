<script setup>
import { onBeforeUnmount, onMounted } from "vue";
import { useRouter } from "vue-router";

import { useAppContext } from "../../../app/bootstrap";
import { useJobs } from "../../../composables/useJobs";
import JobsView from "../../../views/JobsView.vue";

const { api } = useAppContext();
const router = useRouter();
const jobs = useJobs(api.apiFetch);

function openDocument(documentId) {
  return router.push({
    name: "documents",
    query: { document: String(documentId) }
  });
}

onMounted(jobs.startPolling);
onBeforeUnmount(jobs.stopPolling);
</script>

<template>
  <JobsView
    :jobs="jobs.jobs.value"
    :loading="jobs.loading.value"
    :error="jobs.error.value"
    :cancelling-id="jobs.cancellingId.value"
    @refresh="jobs.loadJobs"
    @cancel="jobs.cancelJob"
    @open-document="openDocument"
  />
</template>
