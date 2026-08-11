<script setup>
import { computed } from "vue";

const props = defineProps({
  jobs: { type: Array, required: true },
  loading: Boolean,
  error: { type: String, default: "" },
  cancellingId: { type: String, default: null }
});

const emit = defineEmits(["refresh", "cancel", "open-document"]);

const counts = computed(() => ({
  active: props.jobs.filter((job) => ["queued", "running"].includes(job.status)).length,
  completed: props.jobs.filter((job) => job.status === "completed").length,
  failed: props.jobs.filter((job) => job.status === "failed").length
}));

function statusType(status) {
  return { queued: "warning", running: "info", completed: "success", failed: "error", cancelled: "default" }[status] || "default";
}

function formatDate(value) {
  return value ? new Intl.DateTimeFormat("tr-TR", { dateStyle: "short", timeStyle: "medium" }).format(new Date(value)) : "-";
}
</script>

<template>
  <div class="jobs-view">
    <div class="page-heading jobs-heading">
      <div>
        <p>İşlem Merkezi</p>
        <h1>Joblarım</h1>
        <span>Uzun süren işlemler arka planda çalışır. Burada yalnızca size ait joblar gösterilir.</span>
      </div>
      <n-button :loading="loading" @click="emit('refresh')">Yenile</n-button>
    </div>

    <n-grid :cols="3" :x-gap="16" responsive="screen" item-responsive>
      <n-grid-item span="3 m:1"><n-card size="small"><n-statistic label="Sırada / çalışıyor" :value="counts.active" /></n-card></n-grid-item>
      <n-grid-item span="3 m:1"><n-card size="small"><n-statistic label="Tamamlanan" :value="counts.completed" /></n-card></n-grid-item>
      <n-grid-item span="3 m:1"><n-card size="small"><n-statistic label="Başarısız" :value="counts.failed" /></n-card></n-grid-item>
    </n-grid>

    <n-alert v-if="error" type="error" title="Job listesi alınamadı">{{ error }}</n-alert>

    <n-card title="Son joblar" size="small">
      <n-spin :show="loading">
        <n-empty v-if="jobs.length === 0" description="Henüz bir jobınız yok" />
        <n-list v-else bordered>
          <n-list-item v-for="job in jobs" :key="job.id">
            <div class="job-row">
              <div class="job-main">
                <n-space align="center">
                  <strong>{{ job.job_type_display }}</strong>
                  <n-tag size="small" :type="statusType(job.status)">{{ job.status_display }}</n-tag>
                </n-space>
                <span>{{ job.document_name || `Job ${job.id}` }}</span>
                <small>{{ formatDate(job.created_at) }} · Deneme {{ job.attempts }}/{{ job.max_attempts }}</small>
                <n-progress
                  v-if="job.status === 'running'"
                  type="line"
                  :percentage="job.progress"
                  :height="8"
                  :border-radius="4"
                  processing
                />
                <n-alert v-if="job.error_message" :type="job.status === 'failed' ? 'error' : 'warning'" :show-icon="false">
                  {{ job.error_message }}
                </n-alert>
              </div>
              <n-space class="job-actions">
                <n-button v-if="job.document" size="small" secondary @click="emit('open-document', job.document)">Belgeyi aç</n-button>
                <n-button
                  v-if="job.status === 'queued'"
                  size="small"
                  type="error"
                  secondary
                  :loading="cancellingId === job.id"
                  @click="emit('cancel', job)"
                >İptal et</n-button>
              </n-space>
            </div>
          </n-list-item>
        </n-list>
      </n-spin>
    </n-card>
  </div>
</template>
