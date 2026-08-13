<script setup>
import { computed, h } from "vue";
import { Download, FileText, Pencil, Search, Trash2 } from "@lucide/vue";
import { NButton, NIcon, NSpace, NTag, NText, NTooltip } from "naive-ui";

import { FORM_PROCESS_STATUSES, FORM_PROCESS_STATUS_TAGS } from "../model/options";

const props = defineProps({
  records: { type: Array, required: true },
  processes: { type: Array, required: true },
  templates: { type: Array, required: true },
  filters: { type: Object, required: true },
  loading: { type: Boolean, required: true }
});

const emit = defineEmits(["download", "edit", "delete"]);

function iconButton(icon, title, onClick, type) {
  return h(NTooltip, null, {
    trigger: () =>
      h(
        NButton,
        { circle: true, quaternary: true, size: "small", type, "aria-label": title, onClick },
        { icon: () => h(NIcon, null, { default: () => h(icon, { size: 17 }) }) }
      ),
    default: () => title
  });
}

const columns = [
  {
    title: "Kayıt",
    key: "record_number",
    minWidth: 220,
    render: (record) =>
      h(
        NSpace,
        { vertical: true, size: 2 },
        {
          default: () => [
            h(NText, { strong: true, type: "primary" }, { default: () => record.record_number }),
            h(NText, null, { default: () => record.title })
          ]
        }
      )
  },
  {
    title: "Süreç / Form",
    key: "process_name",
    minWidth: 270,
    render: (record) =>
      h(
        NSpace,
        { vertical: true, size: 3 },
        {
          default: () => [
            h(NTag, { size: "small", bordered: false }, { default: () => record.process_name }),
            h(
              NText,
              { depth: 3 },
              { default: () => `${record.form_number} — ${record.template_title}` }
            )
          ]
        }
      )
  },
  {
    title: "Durum",
    key: "status",
    width: 130,
    render: (record) =>
      h(
        NTag,
        { type: FORM_PROCESS_STATUS_TAGS[record.status], bordered: false },
        { default: () => record.status_display }
      )
  },
  {
    title: "Güncelleyen",
    key: "updated_by_name",
    width: 160,
    render: (record) => h(NText, { depth: 2 }, { default: () => record.updated_by_name || "—" })
  },
  {
    title: "İşlemler",
    key: "actions",
    width: 205,
    align: "right",
    render: (record) =>
      h(
        NSpace,
        { justify: "end", size: 2 },
        {
          default: () => [
            h(
              NButton,
              {
                size: "small",
                secondary: true,
                type: "primary",
                onClick: () => emit("download", record)
              },
              {
                icon: () => h(NIcon, null, { default: () => h(Download, { size: 16 }) }),
                default: () => "Word"
              }
            ),
            iconButton(Pencil, "Kaydı düzenle", () => emit("edit", record)),
            iconButton(Trash2, "Kaydı sil", () => emit("delete", record), "error")
          ]
        }
      )
  }
];

const processOptions = computed(() =>
  props.processes.map((process) => ({ label: process.name, value: process.code }))
);
const templateOptions = computed(() =>
  props.templates.map((template) => ({
    label: `${template.form_number} — ${template.title}`,
    value: template.code
  }))
);
</script>

<template>
  <n-card class="form-process-table-card" content-style="padding: 0">
    <n-grid
      class="form-process-filters"
      cols="1 s:2 l:4"
      responsive="screen"
      :x-gap="10"
      :y-gap="10"
    >
      <n-grid-item>
        <n-input v-model:value="filters.search" clearable placeholder="Kayıt no veya başlık ara…">
          <template #prefix
            ><n-icon><Search /></n-icon
          ></template>
        </n-input>
      </n-grid-item>
      <n-grid-item>
        <n-select
          v-model:value="filters.process"
          :options="processOptions"
          clearable
          placeholder="Tüm süreçler"
        />
      </n-grid-item>
      <n-grid-item>
        <n-select
          v-model:value="filters.template"
          :options="templateOptions"
          clearable
          filterable
          placeholder="Tüm FM formları"
        />
      </n-grid-item>
      <n-grid-item>
        <n-select
          v-model:value="filters.status"
          :options="FORM_PROCESS_STATUSES"
          clearable
          placeholder="Tüm durumlar"
        />
      </n-grid-item>
    </n-grid>
    <n-data-table
      class="form-process-data-table"
      :columns="columns"
      :data="records"
      :loading="loading"
      :pagination="{ pageSize: 10, showSizePicker: true, pageSizes: [10, 20, 50] }"
      :scroll-x="1000"
      :row-key="(record) => record.id"
    >
      <template #empty>
        <n-empty description="Bu filtrelerde form kaydı bulunamadı">
          <template #icon
            ><n-icon><FileText /></n-icon
          ></template>
        </n-empty>
      </template>
    </n-data-table>
  </n-card>
</template>
