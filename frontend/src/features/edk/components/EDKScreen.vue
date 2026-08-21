<script setup>
import { computed, ref } from "vue";

import EDKApplicationsTable from "./EDKApplicationsTable.vue";

const props = defineProps({
  applications: { type: Array, default: () => [] },
  applicationsLoading: Boolean,
  applicationSubmitting: Boolean,
  projects: { type: Array, default: () => [] },
  projectsLoading: Boolean,
  edkRoles: { type: Array, default: () => [] },
  error: { type: String, default: "" }
});

const emit = defineEmits(["create-application", "select-application"]);

function initialApplication() {
  const scheduledAt = new Date();
  scheduledAt.setDate(scheduledAt.getDate() + 7);
  scheduledAt.setSeconds(0, 0);
  return {
    aircraft_name: "",
    tail_number: "",
    scope: "",
    project: null,
    scheduled_at: scheduledAt.getTime()
  };
}

const applicationForm = ref(initialApplication());
const presentationFiles = ref([]);
const isApplicant = computed(() => props.edkRoles.includes("applicant"));
const isApprover = computed(() => props.edkRoles.includes("approver"));
const hasEDKRole = computed(() => isApplicant.value || isApprover.value);
const formReady = computed(() => applicationForm.value.aircraft_name.trim());
const projectOptions = computed(() =>
  props.projects
    .filter((project) => project.is_active)
    .map((project) => ({
      label: `${project.code} — ${project.name}`,
      value: project.id
    }))
);

function minimumScheduledDate() {
  const minimum = new Date();
  minimum.setHours(0, 0, 0, 0);
  minimum.setDate(minimum.getDate() + 7);
  return minimum;
}

function isDateDisabled(timestamp) {
  return timestamp < minimumScheduledDate().getTime();
}

function submitApplication() {
  if (!formReady.value) return;
  emit("create-application", {
    application: {
      ...applicationForm.value,
      scheduled_at: applicationForm.value.scheduled_at
        ? new Date(applicationForm.value.scheduled_at).toISOString()
        : null,
      presentation: presentationFiles.value[0]?.file || null
    },
    onSuccess: () => {
      applicationForm.value = initialApplication();
      presentationFiles.value = [];
    }
  });
}
</script>

<template>
  <section class="edk-view">
    <div class="page-heading edk-heading">
      <p>Emniyet Değerlendirme Kurulu</p>
      <h1>EDK</h1>
      <span>
        EDK başvurularınızı oluşturun, filtreleyin ve ayrıntılı süreç bilgilerine tek ekrandan
        ulaşın.
      </span>
      <n-space class="edk-role-tags" size="small">
        <n-tag v-if="isApplicant" type="info">Başvuru Sahibi</n-tag>
        <n-tag v-if="isApprover" type="success">Onaylayıcı</n-tag>
      </n-space>
    </div>

    <n-alert v-if="!hasEDKRole" type="warning" title="EDK rolü gerekli">
      Bu uygulamayı kullanabilmek için yöneticinizin hesabınıza Başvuru Sahibi veya Onaylayıcı rolü
      ataması gerekir.
    </n-alert>
    <n-alert v-if="error" type="error" title="İşlem başarısız">{{ error }}</n-alert>

    <n-card v-if="isApplicant" title="Yeni EDK Başvurusu" size="small">
      <n-form label-placement="top">
        <n-grid cols="1 720:2" :x-gap="16">
          <n-form-item-gi label="Uçak İsmi" required>
            <n-input
              v-model:value="applicationForm.aircraft_name"
              maxlength="160"
              show-count
              placeholder="Örn. Hürkuş"
            />
          </n-form-item-gi>
          <n-form-item-gi label="Kuyruk Numarası">
            <n-input
              v-model:value="applicationForm.tail_number"
              maxlength="80"
              show-count
              placeholder="Örn. TC-UAV"
            />
          </n-form-item-gi>
          <n-form-item-gi label="Proje">
            <n-select
              v-model:value="applicationForm.project"
              :options="projectOptions"
              :loading="projectsLoading"
              clearable
              filterable
              placeholder="Organizasyon projesi seçin"
            />
          </n-form-item-gi>
          <n-form-item-gi label="Tarih ve Saat">
            <n-date-picker
              v-model:value="applicationForm.scheduled_at"
              type="datetime"
              :is-date-disabled="isDateDisabled"
              clearable
              style="width: 100%"
            />
          </n-form-item-gi>
        </n-grid>
        <n-form-item label="Scope">
          <n-input
            v-model:value="applicationForm.scope"
            type="textarea"
            maxlength="5000"
            show-count
            placeholder="Talebin kapsamını yazın"
          />
        </n-form-item>
        <n-form-item label="Sunum">
          <n-upload
            v-model:file-list="presentationFiles"
            :default-upload="false"
            :max="1"
            accept=".pdf,.docx,.xlsx,.pptx,.txt,.csv,.md,.png,.jpg,.jpeg,.webp,.bmp,.tif,.tiff"
          >
            <n-upload-dragger>
              <div class="upload-title">Sunum dosyasını buraya bırakın veya seçin</div>
              <div class="upload-subtitle">
                Desteklenen doküman ve görsel biçimleri · en fazla 25 MB
              </div>
            </n-upload-dragger>
          </n-upload>
        </n-form-item>
        <n-space justify="end">
          <n-button
            type="primary"
            :loading="applicationSubmitting"
            :disabled="!formReady"
            @click="submitApplication"
          >
            Başvuruyu Onaya Gönder
          </n-button>
        </n-space>
      </n-form>
    </n-card>

    <n-card
      :title="isApprover ? 'EDK Başvuruları' : 'Başvurularım'"
      size="small"
      content-style="padding: 0"
    >
      <EDKApplicationsTable
        :applications="applications"
        :loading="applicationsLoading"
        :show-applicant-filter="isApprover"
        @select="emit('select-application', $event)"
      />
    </n-card>
  </section>
</template>
