<script setup>
import { computed, ref } from "vue";
import { FileText, Search } from "@lucide/vue";

import { filterFormTemplates } from "../model/selectors";

const props = defineProps({
  processes: { type: Array, required: true },
  templates: { type: Array, required: true },
  processCode: { type: String, default: "" },
  templateCode: { type: String, default: "" },
  error: { type: String, default: "" }
});

const emit = defineEmits(["select-process", "select-template"]);
const search = ref("");
const visibleTemplates = computed(() =>
  filterFormTemplates(props.templates, props.processCode, search.value)
);
</script>

<template>
  <div class="form-process-selection-grid">
    <n-card title="1. Süreci seçin" size="small">
      <div class="form-process-choice-list">
        <button
          v-for="process in processes"
          :key="process.code"
          type="button"
          class="form-process-choice"
          :class="{ 'is-selected': process.code === processCode }"
          :aria-pressed="process.code === processCode"
          @click="emit('select-process', process.code)"
        >
          <span>{{ process.name }}</span>
          <n-tag size="small" :bordered="false">{{ process.templates.length }} form</n-tag>
        </button>
      </div>
    </n-card>

    <n-card title="2. FM şablonunu seçin" size="small">
      <n-input v-model:value="search" clearable placeholder="Form numarası veya adı ara…">
        <template #prefix
          ><n-icon><Search /></n-icon
        ></template>
      </n-input>
      <n-alert v-if="error" type="error" class="form-process-alert">{{ error }}</n-alert>
      <div v-if="processCode" class="form-template-choice-list">
        <button
          v-for="template in visibleTemplates"
          :key="template.code"
          type="button"
          class="form-template-choice"
          :class="{ 'is-selected': template.code === templateCode }"
          :aria-pressed="template.code === templateCode"
          @click="emit('select-template', template.code)"
        >
          <n-icon :size="20"><FileText /></n-icon>
          <span>
            <strong>{{ template.form_number }}</strong>
            <small>{{ template.title }}</small>
            <small>{{ template.description }}</small>
          </span>
        </button>
        <n-empty v-if="!visibleTemplates.length" description="Aramayla eşleşen FM şablonu yok" />
      </div>
      <n-empty v-else description="Önce soldan bir süreç seçin" />
    </n-card>
  </div>
</template>
