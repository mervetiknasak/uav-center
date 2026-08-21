<script setup>
import { toRef } from "vue";
import { FileText, Plus, RefreshCw } from "@lucide/vue";

import { useFormProcessController } from "../composables/useFormProcessController";
import FormProcessTable from "./FormProcessTable.vue";

const props = defineProps({
  records: { type: Array, required: true },
  processes: { type: Array, required: true },
  loading: { type: Boolean, required: true },
  error: { type: String, default: "" },
  notice: { type: String, default: "" },
  deepLinkError: { type: String, default: "" }
});

const emit = defineEmits(["refresh", "create", "edit", "status", "delete"]);
const controller = useFormProcessController({
  records: toRef(props, "records"),
  processes: toRef(props, "processes"),
  onEdit: (record) => emit("edit", record),
  onDelete: (record) => emit("delete", record),
  onStatus: (record, status) => emit("status", record, status)
});
</script>

<template>
  <section id="flight-permits" class="form-processes-view">
    <header class="process-section-header">
      <div>
        <n-space align="center" :size="6">
          <n-icon :size="18"><FileText /></n-icon>
          <n-text class="process-section-title" strong>Mühendislik Formları</n-text>
        </n-space>
        <n-text depth="3">
          Klasör bazlı süreçleri, FM Word şablonlarını ve oluşturulan kayıtları yönetin.
        </n-text>
      </div>
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
          @click="emit('create')"
        >
          <template #icon
            ><n-icon><Plus /></n-icon
          ></template>
          Yeni form kaydı
        </n-button>
      </n-space>
    </header>

    <n-alert v-if="error" type="error" title="İşlem tamamlanamadı">{{ error }}</n-alert>
    <n-alert v-if="notice" type="success">{{ notice }}</n-alert>
    <n-alert v-if="deepLinkError" type="warning" title="Kayıt açılamadı">
      {{ deepLinkError }}
    </n-alert>

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
      @edit="controller.edit"
      @archive="controller.requestArchive"
      @reopen="controller.reopen"
      @delete="controller.requestDelete"
    />
  </section>
</template>
