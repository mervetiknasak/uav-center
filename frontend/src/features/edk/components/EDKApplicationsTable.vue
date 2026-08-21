<script setup>
import { computed, h, reactive } from "vue";
import { Search } from "@lucide/vue";
import { NIcon, NSpace, NTag, NText } from "naive-ui";

import {
  EDK_STATUS_OPTIONS,
  EDK_STATUS_TAG_TYPES,
  filterEdkApplications,
  formatEdkDateTime
} from "../model/applications";

const props = defineProps({
  applications: { type: Array, default: () => [] },
  loading: Boolean,
  showApplicantFilter: Boolean
});

const emit = defineEmits(["select"]);
const filters = reactive({ search: "", status: null, applicant: null });

const applicantOptions = computed(() =>
  [...new Set(props.applications.map((item) => item.applicant_name).filter(Boolean))]
    .sort((left, right) => left.localeCompare(right, "tr"))
    .map((value) => ({ label: value, value }))
);
const filteredApplications = computed(() => filterEdkApplications(props.applications, filters));

const columns = [
  {
    title: "Başvuru",
    key: "aircraft_name",
    minWidth: 260,
    render: (application) =>
      h(
        NSpace,
        { vertical: true, size: 2 },
        {
          default: () => [
            h(NText, { strong: true, type: "primary" }, { default: () => `EDK-${application.id}` }),
            h(NText, null, { default: () => application.aircraft_name })
          ]
        }
      )
  },
  { title: "Kuyruk No", key: "tail_number", minWidth: 130 },
  { title: "Proje", key: "project_display", minWidth: 170 },
  { title: "Başvuru Sahibi", key: "applicant_name", minWidth: 150 },
  {
    title: "Tarih ve Saat",
    key: "scheduled_at",
    width: 160,
    render: (application) => formatEdkDateTime(application.scheduled_at)
  },
  {
    title: "Durum",
    key: "status",
    width: 140,
    render: (application) =>
      h(
        NTag,
        { type: EDK_STATUS_TAG_TYPES[application.status], bordered: false, size: "small" },
        { default: () => application.status_display }
      )
  },
  {
    title: "Güncellendi",
    key: "updated_at",
    width: 160,
    render: (application) => formatEdkDateTime(application.updated_at)
  }
];

function rowProps(application) {
  return {
    class: "edk-table-row",
    tabindex: 0,
    "aria-label": `EDK-${application.id} başvurusunu aç`,
    onClick: () => emit("select", application),
    onKeydown: (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        emit("select", application);
      }
    }
  };
}
</script>

<template>
  <div class="edk-table-wrap">
    <n-grid class="edk-table-filters" cols="1 s:2 l:3" responsive="screen" :x-gap="10" :y-gap="10">
      <n-grid-item>
        <n-input
          v-model:value="filters.search"
          clearable
          placeholder="EDK no, uçak, kuyruk no, proje veya scope ara…"
        >
          <template #prefix
            ><n-icon><Search /></n-icon
          ></template>
        </n-input>
      </n-grid-item>
      <n-grid-item>
        <n-select
          v-model:value="filters.status"
          :options="EDK_STATUS_OPTIONS"
          clearable
          placeholder="Tüm durumlar"
        />
      </n-grid-item>
      <n-grid-item v-if="showApplicantFilter">
        <n-select
          v-model:value="filters.applicant"
          :options="applicantOptions"
          clearable
          filterable
          placeholder="Tüm başvuru sahipleri"
        />
      </n-grid-item>
    </n-grid>
    <n-data-table
      :columns="columns"
      :data="filteredApplications"
      :loading="loading"
      :pagination="{ pageSize: 10, showSizePicker: true, pageSizes: [10, 20, 50] }"
      :row-key="(application) => application.id"
      :row-props="rowProps"
      :scroll-x="1220"
    >
      <template #empty>
        <n-empty description="Bu filtrelere uygun EDK başvurusu bulunamadı" />
      </template>
    </n-data-table>
  </div>
</template>
