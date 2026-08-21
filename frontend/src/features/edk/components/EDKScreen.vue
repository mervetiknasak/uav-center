<script setup>
import { computed, reactive, ref, watch } from "vue";
import { Trash2 } from "@lucide/vue";

const props = defineProps({
  applications: { type: Array, default: () => [] },
  applicationsLoading: Boolean,
  applicationSubmitting: Boolean,
  decisionLoadingId: { type: Number, default: null },
  edkRoles: { type: Array, default: () => [] },
  currentUserName: { type: String, default: "" },
  loading: Boolean,
  publishing: Boolean,
  error: { type: String, default: "" },
  result: { type: Object, default: null },
  publishResult: { type: Object, default: null },
  canPublish: { type: Boolean, default: false }
});

const emit = defineEmits(["create-application", "decide", "parse", "publish"]);
const selectedFileNames = reactive({});
const decisionNotes = reactive({});
const draft = ref(null);

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

watch(
  () => props.result,
  (result) => {
    draft.value = result?.jira_draft ? JSON.parse(JSON.stringify(result.jira_draft)) : null;
  },
  { immediate: true }
);

const enabledSubtasks = computed(
  () => draft.value?.subtasks.filter((item) => item.enabled).length || 0
);
const enabledMeetingFields = computed(
  () => draft.value?.task.meeting_fields.filter((field) => field.enabled).length || 0
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

function parseFile({ file, onFinish, onError }, applicationId) {
  selectedFileNames[applicationId] = file.name;
  emit("parse", { applicationId, file: file.file, onFinish, onError });
}

function removeSubtask(index) {
  draft.value.subtasks.splice(index, 1);
}

function setAllMeetingFields(enabled) {
  draft.value.task.meeting_fields.forEach((field) => {
    field.enabled = enabled;
  });
}

function publish() {
  if (props.canPublish) emit("publish", JSON.parse(JSON.stringify(draft.value)));
}

function statusType(status) {
  return { pending: "warning", approved: "success", rejected: "error" }[status] || "default";
}
</script>

<template>
  <section class="edk-view">
    <div class="page-heading edk-heading">
      <p>Elektronik Değerlendirme ve Karar</p>
      <h1>EDK</h1>
      <span>
        Önce EDK başvurunuzu oluşturun. Onaylanan başvurularda toplantı tutanağı yükleme alanı
        otomatik olarak açılır.
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

    <n-card :title="isApprover ? 'EDK Başvuruları' : 'Başvurularım'" size="small">
      <n-spin :show="applicationsLoading">
        <n-empty v-if="!applications.length" description="Henüz EDK başvurusu yok" />
        <div v-else class="edk-application-list">
          <n-card
            v-for="application in applications"
            :key="application.id"
            embedded
            size="small"
            class="edk-application-card"
          >
            <template #header>
              <n-space align="center">
                <strong>EDK-{{ application.id }} · {{ application.meeting_title }}</strong>
                <n-tag :type="statusType(application.status)" size="small">
                  {{ application.status_display }}
                </n-tag>
              </n-space>
            </template>
            <n-descriptions label-placement="top" :columns="2" bordered size="small">
              <n-descriptions-item label="Başvuru Sahibi">
                {{ application.applicant_name }}
              </n-descriptions-item>
              <n-descriptions-item label="Proje">{{
                application.project_name
              }}</n-descriptions-item>
              <n-descriptions-item label="Planlanan Tarih">
                {{ application.requested_date }}
              </n-descriptions-item>
              <n-descriptions-item label="Yer">{{ application.location }}</n-descriptions-item>
              <n-descriptions-item label="Katılımcılar">
                {{ application.participants }}
              </n-descriptions-item>
              <n-descriptions-item label="Amaç">{{ application.purpose }}</n-descriptions-item>
              <n-descriptions-item label="Gündem" :span="2">
                {{ application.agenda }}
              </n-descriptions-item>
            </n-descriptions>

            <n-alert
              v-if="application.decision_note"
              :type="application.status === 'rejected' ? 'error' : 'info'"
              :title="application.status === 'rejected' ? 'Ret Gerekçesi' : 'Onay Notu'"
            >
              {{ application.decision_note }}
            </n-alert>

            <div v-if="isApprover && application.status === 'pending'" class="edk-decision-row">
              <n-input
                v-model:value="decisionNotes[application.id]"
                placeholder="Onay notu veya reddetme gerekçesi"
              />
              <n-button
                type="success"
                secondary
                :disabled="application.applicant_name === currentUserName"
                :loading="decisionLoadingId === application.id"
                @click="
                  emit('decide', application, 'approved', decisionNotes[application.id] || '')
                "
              >
                Onayla
              </n-button>
              <n-button
                type="error"
                secondary
                :disabled="
                  application.applicant_name === currentUserName ||
                  !decisionNotes[application.id]?.trim()
                "
                :loading="decisionLoadingId === application.id"
                @click="emit('decide', application, 'rejected', decisionNotes[application.id])"
              >
                Reddet
              </n-button>
            </div>

            <n-card
              v-if="application.can_upload_minutes"
              title="Toplantı Tutanağı"
              embedded
              size="small"
              class="edk-minutes-upload"
            >
              <n-upload
                directory-dnd
                :max="1"
                accept=".docx"
                :custom-request="(request) => parseFile(request, application.id)"
                :disabled="loading"
              >
                <n-upload-dragger>
                  <div class="upload-title">Onaylı EDK toplantı tutanağını buraya bırakın</div>
                  <div class="upload-subtitle">
                    {{
                      selectedFileNames[application.id] ||
                      application.minutes_file_name ||
                      "Desteklenen dosya biçimi: .docx"
                    }}
                  </div>
                </n-upload-dragger>
              </n-upload>
            </n-card>
          </n-card>
        </div>
      </n-spin>
    </n-card>

    <template v-if="draft">
      <n-alert type="success" title="Toplantı tutanağı işlendi">
        {{ result.file_name }} dosyası EDK-{{ result.application_id }} başvurusu için okundu.
      </n-alert>
      <n-alert v-for="warning in draft.warnings" :key="warning" type="warning" show-icon>
        {{ warning }}
      </n-alert>

      <n-card title="Jira Ana Task Taslağı" size="small">
        <n-grid cols="1 700:3" :x-gap="14">
          <n-form-item-gi label="Jira Proje Anahtarı" required>
            <n-input v-model:value="draft.task.project_key" />
          </n-form-item-gi>
          <n-form-item-gi label="Issue Type">
            <n-input v-model:value="draft.task.issue_type" />
          </n-form-item-gi>
          <n-form-item-gi label="Özet" required>
            <n-input v-model:value="draft.task.summary" />
          </n-form-item-gi>
        </n-grid>
        <n-divider />
        <n-card
          embedded
          size="small"
          :title="`Task açıklamasına eklenecek tutanak alanları (${enabledMeetingFields}/${draft.task.meeting_fields.length})`"
        >
          <template #header-extra>
            <n-button-group size="small">
              <n-button @click="setAllMeetingFields(true)">Tümünü Seç</n-button>
              <n-button @click="setAllMeetingFields(false)">Temizle</n-button>
            </n-button-group>
          </template>
          <div class="meeting-fields">
            <div
              v-for="field in draft.task.meeting_fields"
              :key="field.key"
              class="meeting-field-row"
              :class="{ 'meeting-field-row-disabled': !field.enabled }"
            >
              <div class="meeting-field-label">
                <n-checkbox v-model:checked="field.enabled">{{ field.label }}</n-checkbox>
              </div>
              <div class="meeting-field-value">
                <n-input
                  v-model:value="field.value"
                  type="textarea"
                  autosize
                  :disabled="!field.enabled"
                />
              </div>
            </div>
          </div>
        </n-card>
      </n-card>

      <n-card
        :title="`Sub-task Taslakları (${enabledSubtasks}/${draft.subtasks.length})`"
        size="small"
      >
        <n-empty v-if="!draft.subtasks.length" description="Aksiyon maddesi bulunamadı" />
        <n-collapse v-else>
          <n-collapse-item
            v-for="(item, index) in draft.subtasks"
            :key="item.client_id"
            :name="item.client_id"
          >
            <template #header>
              <n-space align="center">
                <n-checkbox v-model:checked="item.enabled" @click.stop />
                <strong>{{ item.summary || `Sub-task ${index + 1}` }}</strong>
                <n-tag v-if="item.username" type="success" size="small">
                  {{ item.username }}
                </n-tag>
                <n-tag v-else-if="item.responsible" type="warning" size="small">
                  {{ item.responsible }} eşleşmedi
                </n-tag>
              </n-space>
            </template>
            <template #header-extra>
              <n-button circle quaternary type="error" @click.stop="removeSubtask(index)">
                <template #icon><Trash2 :size="15" /></template>
              </n-button>
            </template>
            <n-form :disabled="!item.enabled">
              <n-form-item label="Özet" required>
                <n-input v-model:value="item.summary" />
              </n-form-item>
              <n-form-item label="Açıklama">
                <n-input v-model:value="item.description" type="textarea" />
              </n-form-item>
              <n-grid cols="1 650:3" :x-gap="14">
                <n-form-item-gi label="Tutanaktaki Sorumlu">
                  <n-input v-model:value="item.responsible" />
                </n-form-item-gi>
                <n-form-item-gi label="Username">
                  <n-input v-model:value="item.username" clearable />
                </n-form-item-gi>
                <n-form-item-gi label="Termin Tarihi">
                  <n-input v-model:value="item.due_date" placeholder="YYYY-MM-DD" />
                </n-form-item-gi>
              </n-grid>
            </n-form>
          </n-collapse-item>
        </n-collapse>
      </n-card>

      <n-space v-if="canPublish" justify="end">
        <n-button
          type="primary"
          :loading="publishing"
          :disabled="!draft.task.project_key || !draft.task.summary"
          @click="publish"
        >
          Task ve {{ enabledSubtasks }} Sub-task Oluştur
        </n-button>
      </n-space>
      <n-alert v-else type="info" title="Jira yayınlama yetkisi">
        Jira'da Task ve Sub-task oluşturma yalnızca admin kullanıcılarına açıktır.
      </n-alert>
      <n-alert
        v-if="publishResult"
        :type="['created', 'existing'].includes(publishResult.status) ? 'success' : 'warning'"
        title="Jira aktarım sonucu"
      >
        <div v-if="publishResult.message">{{ publishResult.message }}</div>
        <a :href="publishResult.task.url" target="_blank" rel="noopener noreferrer">
          {{ publishResult.task.key }}
        </a>
      </n-alert>
    </template>
  </section>
</template>
