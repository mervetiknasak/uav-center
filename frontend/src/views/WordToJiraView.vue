<script setup>
import { computed, ref, watch } from "vue";
import { Trash2 } from "@lucide/vue";

const props = defineProps({
  loading: Boolean,
  publishing: Boolean,
  error: { type: String, default: "" },
  result: { type: Object, default: null },
  publishResult: { type: Object, default: null },
  canPublish: { type: Boolean, default: false }
});

const emit = defineEmits(["parse", "publish"]);
const selectedFileName = ref("");
const draft = ref(null);

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
  if (!props.canPublish) return;
  emit("publish", JSON.parse(JSON.stringify(draft.value)));
}
</script>

<template>
  <section class="word-jira-view">
    <div class="page-heading">
      <p>Araçlar</p>
      <h1>Toplantı Tutanağı → Jira</h1>
      <span>Tutanaktan bir ana Task ve her aksiyon maddesi için bir Sub-task hazırlayın.</span>
    </div>

    <n-card title="Toplantı Tutanağı Yükle" size="small">
      <n-upload
        directory-dnd
        :max="1"
        accept=".docx"
        :custom-request="parseFile"
        :disabled="loading"
      >
        <n-upload-dragger>
          <div class="upload-title">Toplantı tutanağını buraya bırakın</div>
          <div class="upload-subtitle">
            {{ selectedFileName || "Desteklenen dosya biçimi: .docx" }}
          </div>
        </n-upload-dragger>
      </n-upload>
      <n-alert v-if="error" type="error" title="İşlem başarısız">{{ error }}</n-alert>
    </n-card>

    <template v-if="draft">
      <n-alert v-for="warning in draft.warnings" :key="warning" type="warning" :show-icon="true">
        {{ warning }}
      </n-alert>

      <n-card title="Ana Task" size="small">
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
                <n-checkbox
                  :checked="field.enabled"
                  @update:checked="(checked) => (field.enabled = checked)"
                >
                  {{ field.label }}
                </n-checkbox>
              </div>
              <div class="meeting-field-value">
                <n-input
                  v-model:value="field.value"
                  type="textarea"
                  autosize
                  :disabled="!field.enabled"
                  :placeholder="`${field.label} bilgisi`"
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
              <n-form-item label="Özet" required
                ><n-input v-model:value="item.summary"
              /></n-form-item>
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
        Taslağı inceleyebilirsiniz. Jira'da Task ve Sub-task oluşturma yalnızca admin
        kullanıcılarına açıktır.
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
        <ul v-if="publishResult.subtasks?.length">
          <li v-for="item in publishResult.subtasks" :key="item.client_id">
            <a v-if="item.url" :href="item.url" target="_blank" rel="noopener noreferrer">
              {{ item.key }}
            </a>
            <span v-else>{{ item.error }}</span>
          </li>
        </ul>
      </n-alert>

      <n-collapse>
        <n-collapse-item title="Teknik okuma detayları" name="details">
          <n-data-table
            :columns="[
              { title: 'Index', key: 'index' },
              { title: 'Tablo', key: 'table_index' },
              { title: 'Satır', key: 'row_index' },
              { title: 'Sütun', key: 'column_index' },
              { title: 'İçerik', key: 'text' }
            ]"
            :data="result.cells"
            :max-height="500"
            virtual-scroll
          />
        </n-collapse-item>
      </n-collapse>
    </template>
  </section>
</template>
