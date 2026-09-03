<script setup>
import { computed, ref, watch } from "vue";
import { Trash2 } from "@lucide/vue";

import { EDK_STATUS_TAG_TYPES, formatEdkDateTime } from "../model/applications";

const props = defineProps({
  application: { type: Object, default: null },
  loading: Boolean,
  decisionLoading: Boolean,
  parseLoading: Boolean,
  publishing: Boolean,
  trackingLoading: Boolean,
  edkRoles: { type: Array, default: () => [] },
  currentUserName: { type: String, default: "" },
  error: { type: String, default: "" },
  result: { type: Object, default: null },
  publishResult: { type: Object, default: null },
  canPublish: Boolean
});

const emit = defineEmits(["back", "decide", "parse", "publish", "refresh-jira"]);
const decisionNote = ref("");
const selectedFileName = ref("");
const draft = ref(null);
const jiraSession = ref("");

const isApprover = computed(() => props.edkRoles.includes("approver"));
const canDecide = computed(
  () =>
    isApprover.value &&
    props.application?.status === "pending" &&
    props.application.applicant_name !== props.currentUserName
);
const enabledSubtasks = computed(
  () => draft.value?.subtasks.filter((item) => item.enabled).length || 0
);
const enabledMeetingFields = computed(
  () => draft.value?.task.meeting_fields.filter((field) => field.enabled).length || 0
);
const jiraTracking = computed(() => props.application?.jira_tracking || null);
const jiraProgress = computed(() => {
  const total = jiraTracking.value?.subtask_total || 0;
  return total ? Math.round((jiraTracking.value.subtask_closed / total) * 100) : 0;
});

watch(
  () => props.result,
  (result) => {
    draft.value = result?.jira_draft ? JSON.parse(JSON.stringify(result.jira_draft)) : null;
  },
  { immediate: true }
);

function parseFile({ file, onFinish, onError }) {
  selectedFileName.value = file.name;
  emit("parse", { file: file.file, onFinish, onError });
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
  if (!props.canPublish || !jiraSession.value.trim()) return;
  emit("publish", {
    ...JSON.parse(JSON.stringify(draft.value)),
    jsession: jiraSession.value.trim()
  });
  jiraSession.value = "";
}
</script>

<template>
  <section class="edk-view edk-detail-view">
    <n-page-header @back="emit('back')">
      <template #title>EDK Başvuru Detayı</template>
      <template #subtitle>Başvurulara dön</template>
    </n-page-header>

    <n-alert v-if="error" type="error" title="İşlem başarısız">{{ error }}</n-alert>

    <n-spin :show="loading">
      <n-empty v-if="!loading && !application" description="EDK başvurusu bulunamadı" />
      <template v-else-if="application">
        <n-card size="small" class="edk-detail-summary">
          <template #header>
            <n-space align="center">
              <strong>EDK-{{ application.id }} · {{ application.aircraft_name }}</strong>
              <n-tag
                :type="EDK_STATUS_TAG_TYPES[application.status]"
                :bordered="false"
                size="small"
              >
                {{ application.status_display }}
              </n-tag>
            </n-space>
          </template>

          <n-descriptions label-placement="top" :columns="2" bordered size="small">
            <n-descriptions-item label="Başvuru Sahibi">
              {{ application.applicant_name }}
            </n-descriptions-item>
            <n-descriptions-item label="Uçak İsmi">
              {{ application.aircraft_name }}
            </n-descriptions-item>
            <n-descriptions-item label="Kuyruk Numarası">
              {{ application.tail_number || "—" }}
            </n-descriptions-item>
            <n-descriptions-item label="Proje">
              {{ application.project_display || "—" }}
            </n-descriptions-item>
            <n-descriptions-item label="Tarih ve Saat">
              {{ formatEdkDateTime(application.scheduled_at) }}
            </n-descriptions-item>
            <n-descriptions-item label="Scope" :span="2">
              <span class="edk-multiline">{{ application.scope || "—" }}</span>
            </n-descriptions-item>
            <n-descriptions-item label="Sunum" :span="2">
              <a v-if="application.presentation_url" :href="application.presentation_url">
                {{ application.presentation_file_name }}
              </a>
              <span v-else>—</span>
            </n-descriptions-item>
            <n-descriptions-item label="Oluşturulma">
              {{ formatEdkDateTime(application.created_at) }}
            </n-descriptions-item>
            <n-descriptions-item label="Son Güncelleme">
              {{ formatEdkDateTime(application.updated_at) }}
            </n-descriptions-item>
          </n-descriptions>
        </n-card>

        <n-card title="Değerlendirme" size="small">
          <n-alert
            v-if="application.status === 'pending'"
            type="warning"
            title="Başvuru onay bekliyor"
          >
            Toplantı tutanağı alanı, başvuru onaylandıktan sonra başvuru sahibine açılır.
          </n-alert>
          <n-alert
            v-else
            :type="application.status === 'rejected' ? 'error' : 'success'"
            :title="application.status === 'rejected' ? 'Başvuru reddedildi' : 'Başvuru onaylandı'"
          >
            <div v-if="application.decision_note" class="edk-multiline">
              {{ application.decision_note }}
            </div>
            <div v-if="application.reviewed_by_name" class="edk-review-meta">
              Değerlendiren: {{ application.reviewed_by_name }} ·
              {{ formatEdkDateTime(application.reviewed_at) }}
            </div>
          </n-alert>

          <div v-if="canDecide" class="edk-decision-row">
            <n-input v-model:value="decisionNote" placeholder="Onay notu veya reddetme gerekçesi" />
            <n-button
              type="success"
              secondary
              :loading="decisionLoading"
              @click="emit('decide', 'approved', decisionNote)"
            >
              Onayla
            </n-button>
            <n-button
              type="error"
              secondary
              :disabled="!decisionNote.trim()"
              :loading="decisionLoading"
              @click="emit('decide', 'rejected', decisionNote)"
            >
              Reddet
            </n-button>
          </div>
          <n-alert
            v-else-if="
              isApprover &&
              application.applicant_name === currentUserName &&
              application.status === 'pending'
            "
            type="info"
            title="Kendi başvurunuz"
          >
            Onaylayıcılar kendi EDK başvurularını karara bağlayamaz.
          </n-alert>
        </n-card>

        <n-card title="Toplantı Tutanağı" size="small" class="edk-minutes-upload">
          <n-descriptions
            v-if="application.minutes_file_name"
            label-placement="left"
            :columns="1"
            bordered
            size="small"
          >
            <n-descriptions-item label="Son yüklenen dosya">
              {{ application.minutes_file_name }}
            </n-descriptions-item>
            <n-descriptions-item label="Yüklenme zamanı">
              {{ formatEdkDateTime(application.minutes_uploaded_at) }}
            </n-descriptions-item>
          </n-descriptions>

          <n-upload
            v-if="application.can_upload_minutes"
            directory-dnd
            :max="1"
            accept=".docx"
            :custom-request="parseFile"
            :disabled="parseLoading"
          >
            <n-upload-dragger>
              <div class="upload-title">Onaylı EDK toplantı tutanağını buraya bırakın</div>
              <div class="upload-subtitle">
                {{
                  selectedFileName ||
                  application.minutes_file_name ||
                  "Desteklenen dosya biçimi: .docx"
                }}
              </div>
            </n-upload-dragger>
          </n-upload>
          <n-alert
            v-else-if="application.status === 'approved'"
            type="info"
            title="Yükleme yetkisi"
          >
            Toplantı tutanağını yalnızca bu başvurunun sahibi yükleyebilir.
          </n-alert>
          <n-alert v-else type="warning" title="Yükleme henüz açık değil">
            Toplantı tutanağı yalnızca onaylanan başvurular için yüklenebilir.
          </n-alert>
        </n-card>

        <n-card v-if="jiraTracking" title="Jira Task Takibi" size="small">
          <template #header-extra>
            <n-button
              size="small"
              secondary
              type="primary"
              :loading="trackingLoading"
              @click="emit('refresh-jira')"
            >
              Jira'dan Yenile
            </n-button>
          </template>

          <n-descriptions label-placement="top" :columns="2" bordered size="small">
            <n-descriptions-item label="Task">
              <a :href="jiraTracking.url" target="_blank" rel="noopener noreferrer">
                {{ jiraTracking.key }}
              </a>
            </n-descriptions-item>
            <n-descriptions-item label="Task Durumu">
              {{ jiraTracking.status || "Henüz alınmadı" }}
            </n-descriptions-item>
            <n-descriptions-item label="Task Özeti" :span="2">
              {{ jiraTracking.summary || "—" }}
            </n-descriptions-item>
            <n-descriptions-item label="Son Jira Kontrolü" :span="2">
              {{
                jiraTracking.last_synced_at
                  ? formatEdkDateTime(jiraTracking.last_synced_at)
                  : "Henüz kontrol edilmedi"
              }}
            </n-descriptions-item>
          </n-descriptions>

          <div class="edk-jira-progress">
            <n-space justify="space-between" align="center">
              <strong>Sub-task kapanma durumu</strong>
              <n-tag
                :type="jiraTracking.all_subtasks_closed ? 'success' : 'warning'"
                :bordered="false"
                size="small"
              >
                {{
                  jiraTracking.all_subtasks_closed
                    ? "Tüm Sub-task'lar kapalı"
                    : `${jiraTracking.subtask_closed}/${jiraTracking.subtask_total} kapalı`
                }}
              </n-tag>
            </n-space>
            <n-progress
              type="line"
              :percentage="jiraProgress"
              :status="jiraTracking.all_subtasks_closed ? 'success' : 'default'"
            />
          </div>

          <n-alert
            v-if="!jiraTracking.subtask_total"
            type="warning"
            title="Takip edilecek Sub-task bulunamadı"
          >
            Tamamlanma koşulu için Jira Task'ının altında en az bir Sub-task bulunmalıdır.
          </n-alert>
          <div v-else class="edk-jira-subtasks">
            <div
              v-for="subtask in jiraTracking.subtasks"
              :key="subtask.key"
              class="edk-jira-subtask"
            >
              <div>
                <a :href="subtask.url" target="_blank" rel="noopener noreferrer">
                  {{ subtask.key }}
                </a>
                <div>{{ subtask.summary }}</div>
              </div>
              <n-tag
                :type="subtask.is_closed ? 'success' : 'warning'"
                :bordered="false"
                size="small"
              >
                {{ subtask.status || (subtask.is_closed ? "Kapalı" : "Açık") }}
              </n-tag>
            </div>
          </div>
        </n-card>
      </template>
    </n-spin>

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

      <n-card v-if="canPublish && !jiraTracking" title="Jira Kullanıcı Oturumu" size="small">
        <n-form-item label="JSESSIONID değeri" required>
          <n-input
            v-model:value="jiraSession"
            type="password"
            show-password-on="click"
            autocomplete="off"
            maxlength="4096"
            placeholder="JSESSIONID çerezinin yalnızca değerini girin"
          />
        </n-form-item>
        <n-alert type="info" :show-icon="false">
          Bu değer yalnızca bu Jira aktarımında sizin adınıza işlem yapmak için kullanılır ve
          kaydedilmez.
        </n-alert>
      </n-card>
      <n-space v-if="canPublish && !jiraTracking" justify="end">
        <n-button
          type="primary"
          :loading="publishing"
          :disabled="!draft.task.project_key || !draft.task.summary || !jiraSession.trim()"
          @click="publish"
        >
          Task ve {{ enabledSubtasks }} Sub-task Oluştur
        </n-button>
      </n-space>
      <n-alert v-else-if="jiraTracking" type="info" title="Jira Task bağlantısı mevcut">
        Bu EDK, {{ jiraTracking.key }} Task'ına bağlıdır. Güncel durumu takip kartından
        yenileyebilirsiniz.
      </n-alert>
      <n-alert v-else type="info" title="Jira yayınlama yetkisi">
        Jira'da Task ve Sub-task oluşturma yalnızca adminlere ve bu EDK talebini açan kişiye
        açıktır.
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
