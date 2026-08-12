<script setup>
import { h } from "vue";
import { NButton, NIcon, NSpace, NTag, NText, NTooltip } from "naive-ui";
import { Download, FileText, Pencil, Plane, Search, Trash2 } from "@lucide/vue";

import { formatFlightPermitDate, formatFlightPermitFileSize } from "../model/formatters";
import {
  FLIGHT_PERMIT_KINDS,
  FLIGHT_PERMIT_VALIDITY_STATUSES,
  FLIGHT_PERMIT_VALIDITY_TAG_TYPES
} from "../model/options";

defineProps({
  permits: { type: Array, required: true },
  filters: { type: Object, required: true },
  serialNumberOptions: { type: Array, required: true },
  loading: { type: Boolean, required: true }
});

const emit = defineEmits(["open-document", "download", "open-editor", "request-delete"]);

function iconButton(icon, title, onClick, options = {}) {
  return h(NTooltip, null, {
    trigger: () =>
      h(
        NButton,
        {
          circle: true,
          quaternary: true,
          size: "small",
          type: options.type,
          disabled: options.disabled,
          "aria-label": title,
          onClick
        },
        { icon: () => h(NIcon, null, { default: () => h(icon, { size: 17 }) }) }
      ),
    default: () => title
  });
}

const columns = [
  {
    title: "Hava aracı",
    key: "serial_number",
    width: 210,
    fixed: "left",
    sorter: (a, b) => (a.serial_number || "").localeCompare(b.serial_number || "", "tr"),
    render: (permit) =>
      h(
        NSpace,
        { align: "center", size: 8 },
        {
          default: () => [
            h(NIcon, { color: "#0f766e", size: 18 }, { default: () => h(Plane) }),
            h(
              NSpace,
              { vertical: true, size: 2 },
              {
                default: () => [
                  h(NText, { strong: true }, { default: () => permit.serial_number || "—" }),
                  h(
                    NText,
                    { depth: 3 },
                    {
                      default: () =>
                        [permit.aircraft_manufacturer, permit.aircraft_type]
                          .filter(Boolean)
                          .join(" / ") || "Üretici / tip belirtilmedi"
                    }
                  )
                ]
              }
            )
          ]
        }
      )
  },
  {
    title: "İzin",
    key: "permit_number",
    width: 210,
    sorter: (a, b) => a.permit_number.localeCompare(b.permit_number, "tr"),
    render: (permit) =>
      h(
        NSpace,
        { vertical: true, size: 3 },
        {
          default: () => [
            h(NText, { strong: true, type: "primary" }, { default: () => permit.permit_number }),
            h(NText, { depth: 3 }, { default: () => permit.permit_applicant }),
            permit.is_recommendation
              ? h(
                  NTag,
                  { size: "tiny", type: "info", bordered: false },
                  { default: () => "Tavsiye" }
                )
              : null
          ]
        }
      )
  },
  {
    title: "Uçuş kapsamı",
    key: "purpose_of_flight",
    width: 240,
    sorter: (a, b) =>
      (a.purpose_of_flight_display || [])
        .join(" ")
        .localeCompare((b.purpose_of_flight_display || []).join(" "), "tr"),
    render: (permit) =>
      h(
        NSpace,
        { vertical: true, size: 3 },
        {
          default: () => [
            h(
              NText,
              { strong: true },
              {
                default: () =>
                  (permit.purpose_of_flight_display || []).join(", ") || "Amaç belirtilmedi"
              }
            ),
            h(
              NText,
              { depth: 3 },
              {
                default: () =>
                  permit.target_date
                    ? `Hedef: ${formatFlightPermitDate(permit.target_date)}${permit.flight_duration ? ` · ${permit.flight_duration} saat` : ""}`
                    : "Hedef tarih belirtilmedi"
              }
            )
          ]
        }
      )
  },
  {
    title: "Geçerlilik",
    key: "valid_until",
    width: 185,
    sorter: (a, b) => a.valid_until.localeCompare(b.valid_until),
    render: (permit) =>
      h(
        NSpace,
        { vertical: true, size: 3 },
        {
          default: () => [
            h(NText, null, { default: () => formatFlightPermitDate(permit.valid_from) }),
            h(
              NText,
              { depth: 3 },
              { default: () => `→ ${formatFlightPermitDate(permit.valid_until)}` }
            )
          ]
        }
      )
  },
  {
    title: "Durum",
    key: "validity_status",
    width: 170,
    render: (permit) =>
      h(
        NTag,
        {
          size: "small",
          bordered: false,
          type: FLIGHT_PERMIT_VALIDITY_TAG_TYPES[permit.validity_status]
        },
        { default: () => permit.validity_status_display }
      )
  },
  {
    title: "Doküman",
    key: "document",
    width: 220,
    render(permit) {
      if (!permit.document_url) return h(NText, { depth: 3 }, { default: () => "Eklenmedi" });
      return h(
        NButton,
        { text: true, type: "primary", onClick: () => emit("open-document", permit) },
        {
          icon: () => h(NIcon, null, { default: () => h(FileText) }),
          default: () =>
            h(
              NSpace,
              { vertical: true, size: 0 },
              {
                default: () => [
                  h(
                    NText,
                    { class: "fp-file-name", type: "primary" },
                    { default: () => permit.document_name }
                  ),
                  h(
                    NText,
                    { depth: 3 },
                    { default: () => formatFlightPermitFileSize(permit.document_size) }
                  )
                ]
              }
            )
        }
      );
    }
  },
  {
    title: "İşlemler",
    key: "actions",
    width: 218,
    fixed: "right",
    align: "right",
    render: (permit) =>
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
                onClick: () => emit("download", permit)
              },
              {
                icon: () => h(NIcon, null, { default: () => h(Download, { size: 16 }) }),
                default: () => "Word indir"
              }
            ),
            iconButton(Pencil, "İzni düzenle", () => emit("open-editor", permit)),
            iconButton(Trash2, "İzni sil", () => emit("request-delete", permit), {
              type: "error"
            })
          ]
        }
      )
  }
];

const pagination = {
  pageSize: 10,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
  showQuickJumper: true
};
</script>

<template>
  <n-card class="fp-table-card" content-style="padding: 0">
    <n-grid class="fp-filter-bar" cols="1 s:2 l:4" responsive="screen" :x-gap="10" :y-gap="10">
      <n-grid-item>
        <n-input
          v-model:value="filters.search"
          clearable
          placeholder="Başvuru sahibi, izin no, seri no veya uçuş amacı ara…"
        >
          <template #prefix
            ><n-icon><Search /></n-icon
          ></template>
        </n-input>
      </n-grid-item>
      <n-grid-item>
        <n-select
          v-model:value="filters.validityStatus"
          clearable
          placeholder="Tüm durumlar"
          :options="FLIGHT_PERMIT_VALIDITY_STATUSES"
        />
      </n-grid-item>
      <n-grid-item>
        <n-select
          v-model:value="filters.recommendation"
          clearable
          placeholder="Tüm belge türleri"
          :options="FLIGHT_PERMIT_KINDS"
        />
      </n-grid-item>
      <n-grid-item>
        <n-select
          v-model:value="filters.serialNumber"
          clearable
          filterable
          placeholder="Tüm seri numaraları"
          :options="serialNumberOptions"
        />
      </n-grid-item>
    </n-grid>

    <n-flex class="fp-table-summary" justify="space-between" align="center">
      <n-text strong>{{ permits.length }} uçuş izni</n-text>
      <n-text :depth="3">Güncel geçerlilik durumuna göre hesaplanır</n-text>
    </n-flex>

    <n-data-table
      class="fp-data-table"
      :columns="columns"
      :data="permits"
      :loading="loading"
      :pagination="pagination"
      :row-key="(permit) => permit.id"
      :scroll-x="1423"
    />
  </n-card>
</template>
