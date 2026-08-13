<script setup>
import { computed } from "vue";

import { FORM_PROCESS_STATUSES } from "../model/options";
import { groupTemplateFields } from "../model/selectors";

const props = defineProps({
  show: { type: Boolean, required: true },
  editingId: { type: Number, default: null },
  form: { type: Object, required: true },
  processes: { type: Array, required: true },
  templates: { type: Array, required: true },
  formError: { type: String, default: "" },
  saving: { type: Boolean, required: true }
});

const emit = defineEmits(["update:show", "change-template", "submit"]);

const selectedTemplate = computed(() =>
  props.templates.find((template) => template.code === props.form.template_code)
);
const templateGroups = computed(() => groupTemplateFields(selectedTemplate.value?.fields || []));
const templateOptions = computed(() =>
  props.templates
    .filter(
      (template) => !props.form.process_code || template.process_code === props.form.process_code
    )
    .map((template) => ({
      label: `${template.form_number} — ${template.title}`,
      value: template.code
    }))
);
const processOptions = computed(() =>
  props.processes.map((process) => ({ label: process.name, value: process.code }))
);

function changeProcess(processCode) {
  const firstTemplate = props.templates.find((template) => template.process_code === processCode);
  if (firstTemplate) emit("change-template", firstTemplate.code);
}
</script>

<template>
  <n-modal
    :show="show"
    preset="card"
    class="form-process-editor"
    :title="editingId ? 'Form kaydını düzenle' : 'Yeni form kaydı'"
    :bordered="false"
    @update:show="emit('update:show', $event)"
  >
    <n-alert v-if="formError" type="error" class="form-process-alert">{{ formError }}</n-alert>
    <n-form label-placement="top">
      <n-alert type="info" :show-icon="false" class="form-process-alert">
        Seçilen klasör bir süreci, FM dokümanı ise sürümlü Word şablonunu temsil eder.
      </n-alert>
      <n-grid cols="1 m:2" responsive="screen" :x-gap="16">
        <n-form-item-gi label="Süreç" required>
          <n-select
            :value="form.process_code"
            :options="processOptions"
            placeholder="Süreç seçin"
            @update:value="changeProcess"
          />
        </n-form-item-gi>
        <n-form-item-gi label="FM şablonu" required>
          <n-select
            :value="form.template_code"
            :options="templateOptions"
            placeholder="Form seçin"
            @update:value="emit('change-template', $event)"
          />
        </n-form-item-gi>
        <n-form-item-gi label="Kayıt numarası" required>
          <n-input v-model:value="form.record_number" placeholder="Örn. PROJE-FM-2026-001" />
        </n-form-item-gi>
        <n-form-item-gi label="Kayıt başlığı" required>
          <n-input v-model:value="form.title" />
        </n-form-item-gi>
        <n-form-item-gi label="Durum" required>
          <n-select v-model:value="form.status" :options="FORM_PROCESS_STATUSES" />
        </n-form-item-gi>
      </n-grid>

      <template v-for="group in templateGroups" :key="group.name">
        <n-divider>{{ group.name }}</n-divider>
        <n-grid cols="1 m:2" responsive="screen" :x-gap="16">
          <n-form-item-gi
            v-for="field in group.fields"
            :key="field.key"
            :label="field.label"
            :required="field.required"
            :span="field.type === 'textarea' ? 2 : 1"
          >
            <n-date-picker
              v-if="field.type === 'date'"
              v-model:formatted-value="form.data[field.key]"
              value-format="yyyy-MM-dd"
              type="date"
              clearable
            />
            <n-select
              v-else-if="field.type === 'select'"
              v-model:value="form.data[field.key]"
              :options="field.options"
              clearable
            />
            <n-input
              v-else
              v-model:value="form.data[field.key]"
              :type="field.type"
              :rows="field.type === 'textarea' ? 4 : undefined"
              :maxlength="field.max_length"
              :placeholder="field.placeholder"
              show-count
            />
          </n-form-item-gi>
        </n-grid>
      </template>

      <n-divider />
      <n-form-item label="Kayıt notları">
        <n-input v-model:value="form.notes" type="textarea" :rows="3" maxlength="10000" />
      </n-form-item>
    </n-form>
    <template #footer>
      <n-flex justify="end">
        <n-button @click="emit('update:show', false)">Vazgeç</n-button>
        <n-button type="primary" :loading="saving" @click="emit('submit')">Kaydet</n-button>
      </n-flex>
    </template>
  </n-modal>
</template>
