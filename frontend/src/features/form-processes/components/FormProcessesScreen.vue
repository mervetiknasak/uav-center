<script setup>
import { toRef } from "vue";
import { Files, Plus, RefreshCw } from "@lucide/vue";

import { useFormProcessController } from "../composables/useFormProcessController";
import FormProcessEditor from "./FormProcessEditor.vue";
import FormProcessTable from "./FormProcessTable.vue";

const props = defineProps({
  records: { type: Array, required: true },
  processes: { type: Array, required: true },
  loading: { type: Boolean, required: true },
  saving: { type: Boolean, required: true },
  error: { type: String, default: "" },
  notice: { type: String, default: "" }
});

const emit = defineEmits(["refresh", "save", "delete"]);
const controller = useFormProcessController({
  records: toRef(props, "records"),
  processes: toRef(props, "processes"),
  onSave: (payload) => emit("save", payload),
  onDelete: (record) => emit("delete", record)
});
</script>

<template>
  <section class="form-processes-view">
    <n-page-header
      title="Mühendislik Form Süreçleri"
      subtitle="Klasör bazlı süreçleri, FM Word şablonlarını ve oluşturulan kayıtları yönetin."
    >
      <template #header>
        <n-space align="center" :size="6">
          <n-icon :size="16"><Files /></n-icon>
          <n-text type="primary" strong>Süreçler</n-text>
        </n-space>
      </template>
      <template #extra>
        <n-space>
          <n-button secondary :loading="loading" @click="emit('refresh')">
            <template #icon
              ><n-icon><RefreshCw /></n-icon
            ></template>
            Yenile
          </n-button>
          <n-button
            type="primary"
            :disabled="!controller.templates.value.length"
            @click="controller.openEditor()"
          >
            <template #icon
              ><n-icon><Plus /></n-icon
            ></template>
            Yeni form kaydı
          </n-button>
        </n-space>
      </template>
    </n-page-header>

    <n-alert v-if="error" type="error" title="Form süreçleri alınamadı">{{ error }}</n-alert>
    <n-alert v-if="notice" type="success">{{ notice }}</n-alert>

    <n-grid cols="1 s:2 l:4" responsive="screen" :x-gap="12" :y-gap="12">
      <n-grid-item>
        <n-card size="small"><n-statistic label="Süreç" :value="processes.length" /></n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card size="small"
          ><n-statistic label="FM şablonu" :value="controller.templates.value.length"
        /></n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card size="small"><n-statistic label="Toplam kayıt" :value="records.length" /></n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card size="small"
          ><n-statistic
            label="Onaylı kayıt"
            :value="records.filter((record) => record.status === 'approved').length"
        /></n-card>
      </n-grid-item>
    </n-grid>

    <FormProcessTable
      :records="controller.filteredRecords.value"
      :processes="processes"
      :templates="controller.templates.value"
      :filters="controller.filters"
      :loading="loading"
      @download="controller.download"
      @edit="controller.openEditor"
      @delete="controller.requestDelete"
    />
    <FormProcessEditor
      v-model:show="controller.showEditor.value"
      :editing-id="controller.editingId.value"
      :form="controller.form"
      :processes="processes"
      :templates="controller.templates.value"
      :form-error="controller.formError.value"
      :saving="saving"
      @change-template="controller.changeTemplate"
      @submit="controller.submit"
    />
  </section>
</template>
