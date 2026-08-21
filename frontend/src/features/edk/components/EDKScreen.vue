<script setup>
import { computed, ref } from "vue";

import EDKApplicationsTable from "./EDKApplicationsTable.vue";

const props = defineProps({
  applications: { type: Array, default: () => [] },
  applicationsLoading: Boolean,
  applicationSubmitting: Boolean,
  edkRoles: { type: Array, default: () => [] },
  error: { type: String, default: "" }
});

const emit = defineEmits(["create-application", "select-application"]);

function initialApplication() {
  const requestedDate = new Date();
  requestedDate.setDate(requestedDate.getDate() + 7);
  return {
    meeting_title: "",
    project_name: "",
    requested_date: requestedDate.getTime(),
    location: "",
    participants: "",
    purpose: "",
    agenda: ""
  };
}

const applicationForm = ref(initialApplication());
const isApplicant = computed(() => props.edkRoles.includes("applicant"));
const isApprover = computed(() => props.edkRoles.includes("approver"));
const hasEDKRole = computed(() => isApplicant.value || isApprover.value);
const formReady = computed(() =>
  [
    applicationForm.value.meeting_title,
    applicationForm.value.project_name,
    applicationForm.value.location,
    applicationForm.value.participants,
    applicationForm.value.purpose,
    applicationForm.value.agenda
  ].every((value) => value.trim())
);

function dateOnly(timestamp) {
  const date = new Date(timestamp);
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${date.getFullYear()}-${month}-${day}`;
}

function submitApplication() {
  if (!formReady.value || !applicationForm.value.requested_date) return;
  emit("create-application", {
    application: {
      ...applicationForm.value,
      requested_date: dateOnly(applicationForm.value.requested_date)
    },
    onSuccess: () => {
      applicationForm.value = initialApplication();
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
          <n-form-item-gi label="Toplantı / EDK Konusu" required>
            <n-input
              v-model:value="applicationForm.meeting_title"
              maxlength="240"
              show-count
              placeholder="Örn. Uçuşa hazırlık değerlendirmesi"
            />
          </n-form-item-gi>
          <n-form-item-gi label="Proje" required>
            <n-input v-model:value="applicationForm.project_name" placeholder="Örn. UAV Merkezi" />
          </n-form-item-gi>
          <n-form-item-gi label="Planlanan Toplantı Tarihi" required>
            <n-date-picker
              v-model:value="applicationForm.requested_date"
              type="date"
              clearable
              style="width: 100%"
            />
          </n-form-item-gi>
          <n-form-item-gi label="Toplantı Yeri" required>
            <n-input
              v-model:value="applicationForm.location"
              placeholder="Örn. Hangar toplantı odası"
            />
          </n-form-item-gi>
        </n-grid>
        <n-form-item label="Katılımcılar" required>
          <n-input
            v-model:value="applicationForm.participants"
            type="textarea"
            placeholder="Katılması planlanan kişi veya ekipler"
          />
        </n-form-item>
        <n-grid cols="1 720:2" :x-gap="16">
          <n-form-item-gi label="Başvuru Amacı" required>
            <n-input v-model:value="applicationForm.purpose" type="textarea" />
          </n-form-item-gi>
          <n-form-item-gi label="Gündem" required>
            <n-input v-model:value="applicationForm.agenda" type="textarea" />
          </n-form-item-gi>
        </n-grid>
        <n-space justify="end">
          <n-button
            type="primary"
            :loading="applicationSubmitting"
            :disabled="!formReady || !applicationForm.requested_date"
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
