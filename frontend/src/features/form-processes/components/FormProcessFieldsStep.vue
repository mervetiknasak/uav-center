<script setup>
import { computed } from "vue";
import { ExternalLink, Paperclip } from "@lucide/vue";

import { groupTemplateFields } from "../model/selectors";
import { FORM_ATTACHMENT_ACCEPT, formatFormAttachmentSize } from "../model/attachment";
import FormProcessTableField from "./FormProcessTableField.vue";

const props = defineProps({
  form: { type: Object, required: true },
  template: { type: Object, required: true },
  errors: { type: Object, default: () => ({}) },
  fileList: { type: Array, required: true },
  existingAttachment: { type: Object, default: null }
});

const emit = defineEmits([
  "update-identity",
  "update-field",
  "update-notes",
  "update:file-list",
  "remove-attachment",
  "open-attachment"
]);
const groups = computed(() => groupTemplateFields(props.template.fields || []));
const errorItems = computed(() => {
  const labels = new Map((props.template.fields || []).map((field) => [field.key, field.label]));
  labels.set("record_number", "Kayıt numarası");
  labels.set("title", "Kayıt başlığı");
  return Object.entries(props.errors)
    .filter(([key]) => key !== "template_code")
    .map(([key, message]) => ({ key, label: labels.get(key) || "Form", message }));
});

function focusError(key) {
  document.getElementById(`fm-field-${key}`)?.focus();
}
</script>

<template>
  <div class="form-process-fields">
    <n-alert v-if="errorItems.length" type="error" title="Düzeltilmesi gereken alanlar">
      <div class="form-process-error-links">
        <button
          v-for="item in errorItems"
          :key="item.key"
          type="button"
          @click="focusError(item.key)"
        >
          {{ item.label }}: {{ item.message }}
        </button>
      </div>
    </n-alert>

    <n-card title="Kayıt bilgileri" size="small">
      <n-grid cols="1 m:2" responsive="screen" :x-gap="16">
        <n-form-item-gi
          label="Kayıt numarası"
          required
          :validation-status="errors.record_number ? 'error' : undefined"
          :feedback="errors.record_number"
        >
          <n-input
            id="fm-field-record_number"
            :value="form.record_number"
            placeholder="Örn. PROJE-FM-2026-001"
            @update:value="emit('update-identity', 'record_number', $event)"
          />
        </n-form-item-gi>
        <n-form-item-gi
          label="Kayıt başlığı"
          required
          :validation-status="errors.title ? 'error' : undefined"
          :feedback="errors.title"
        >
          <n-input
            id="fm-field-title"
            :value="form.title"
            @update:value="emit('update-identity', 'title', $event)"
          />
        </n-form-item-gi>
      </n-grid>
    </n-card>

    <n-card v-for="group in groups" :key="group.name" :title="group.name" size="small">
      <n-grid cols="1 m:2" responsive="screen" :x-gap="16">
        <n-form-item-gi
          v-for="field in group.fields"
          :key="field.key"
          :label="field.label"
          :required="field.required"
          :span="['textarea', 'table'].includes(field.type) ? 2 : 1"
          :validation-status="errors[field.key] ? 'error' : undefined"
          :feedback="errors[field.key]"
        >
          <FormProcessTableField
            v-if="field.type === 'table'"
            :field="field"
            :value="form.data[field.key]"
            @update:value="emit('update-field', field.key, $event)"
          />
          <n-date-picker
            v-else-if="field.type === 'date'"
            :id="`fm-field-${field.key}`"
            :formatted-value="form.data[field.key]"
            value-format="yyyy-MM-dd"
            type="date"
            clearable
            @update:formatted-value="emit('update-field', field.key, $event)"
          />
          <n-select
            v-else-if="['select', 'multi_select'].includes(field.type)"
            :id="`fm-field-${field.key}`"
            :value="form.data[field.key]"
            :options="field.options"
            :multiple="field.type === 'multi_select'"
            clearable
            @update:value="emit('update-field', field.key, $event)"
          />
          <n-input
            v-else
            :id="`fm-field-${field.key}`"
            :value="form.data[field.key]"
            :type="field.type"
            :rows="field.type === 'textarea' ? 4 : undefined"
            :maxlength="field.max_length"
            :placeholder="field.placeholder"
            show-count
            @update:value="emit('update-field', field.key, $event)"
          />
        </n-form-item-gi>
      </n-grid>
    </n-card>

    <n-card title="Kayıt eki" size="small">
      <div class="form-process-upload-area">
        <n-alert v-if="existingAttachment" type="info" :show-icon="false">
          <n-flex justify="space-between" align="center">
            <n-button text type="primary" @click="emit('open-attachment')">
              <template #icon
                ><n-icon><ExternalLink /></n-icon
              ></template>
              {{ existingAttachment.name }} ·
              {{ formatFormAttachmentSize(existingAttachment.size) }}
            </n-button>
            <n-button text type="error" @click="emit('remove-attachment')">Kaldır</n-button>
          </n-flex>
        </n-alert>
        <n-upload
          :file-list="fileList"
          :default-upload="false"
          :max="1"
          :accept="FORM_ATTACHMENT_ACCEPT"
          @update:file-list="emit('update:file-list', $event)"
        >
          <n-upload-dragger>
            <n-icon :size="32" :depth="3"><Paperclip /></n-icon>
            <n-text class="form-process-upload-title"> Dokümanı buraya bırakın veya seçin </n-text>
            <n-text :depth="3">PDF, DOCX, XLSX veya görsel · en fazla 15 MB</n-text>
          </n-upload-dragger>
        </n-upload>
      </div>
    </n-card>

    <n-card title="Kayıt notları" size="small">
      <n-input
        :value="form.notes"
        type="textarea"
        :rows="3"
        maxlength="10000"
        @update:value="emit('update-notes', $event)"
      />
    </n-card>
  </div>
</template>
