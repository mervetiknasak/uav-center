<script setup>
import { computed, h } from "vue";
import { NButton, NIcon, NSelect, NSpace, NTag, NText, NThing, NTooltip } from "naive-ui";
import { Eye, Mail, Pencil, Search, Trash2 } from "@lucide/vue";

import { formatTechnicalDocumentDate, formatTechnicalDocumentDateTime } from "../model/formatters";
import {
  TECHNICAL_DOCUMENT_PRIORITY_TYPES,
  TECHNICAL_DOCUMENT_STATUSES,
  TECHNICAL_DOCUMENT_STATUS_TYPES
} from "../model/options";

const props = defineProps({
  documents: { type: Array, required: true },
  filters: { type: Object, required: true },
  panelOptions: { type: Array, required: true },
  categoryOptions: { type: Array, required: true },
  projectName: { type: String, default: "" },
  loading: { type: Boolean, required: true },
  canEdit: { type: Boolean, default: false },
  notifyingId: { type: Number, default: null },
  isOverdue: { type: Function, required: true }
});

const emit = defineEmits([
  "open-detail",
  "open-notification",
  "open-editor",
  "request-delete",
  "update-status"
]);

function iconButton(icon, title, onClick, options = {}) {
  return h(NTooltip, null, {
    trigger: () =>
      h(
        NButton,
        {
          circle: true,
          quaternary: true,
          size: "small",
          "aria-label": title,
          type: options.type,
          disabled: options.disabled,
          loading: options.loading,
          onClick
        },
        {
          icon: () => h(NIcon, null, { default: () => h(icon, { size: 17 }) })
        }
      ),
    default: () => title
  });
}

const columns = computed(() => [
  {
    title: "Doküman",
    key: "document",
    width: 290,
    fixed: "left",
    sorter: (a, b) => a.code.localeCompare(b.code, "tr"),
    render(document) {
      const codeRow = [
        h(NText, { strong: true, type: "primary" }, { default: () => document.code }),
        document.priority !== "normal"
          ? h(
              NTag,
              { size: "tiny", type: TECHNICAL_DOCUMENT_PRIORITY_TYPES[document.priority] },
              { default: () => document.priority_display }
            )
          : null
      ];
      return h(
        NSpace,
        { class: "td-document-cell", vertical: true, size: 2 },
        {
          default: () => [
            h(NSpace, { size: 6, align: "center" }, { default: () => codeRow }),
            h(
              NButton,
              {
                text: true,
                type: "primary",
                onClick: () => emit("open-detail", document)
              },
              { default: () => document.title }
            ),
            h(
              NText,
              { depth: 3 },
              { default: () => document.category || document.document_type || "Kategorisiz" }
            )
          ]
        }
      );
    }
  },
  {
    title: "Kapak sayfası",
    key: "cover_page",
    width: 145,
    sorter: (a, b) => (a.cover_page?.number || "").localeCompare(b.cover_page?.number || "", "tr"),
    render(document) {
      if (!document.cover_page) return h(NText, { depth: 3 }, { default: () => "—" });
      return h(
        NSpace,
        { vertical: true, size: 1 },
        {
          default: () => [
            h(NText, { strong: true }, { default: () => document.cover_page.number }),
            h(NText, { depth: 3 }, { default: () => `Issue ${document.cover_page.issue}` })
          ]
        }
      );
    }
  },
  {
    title: "Panel kapsamı",
    key: "panels",
    width: 190,
    render(document) {
      const panels = document.panel_details || [];
      if (!panels.length) return h(NText, { depth: 3 }, { default: () => "Proje geneli" });
      const tags = panels
        .slice(0, 2)
        .map((panel) =>
          h(NTag, { key: panel.id, size: "small", bordered: false }, { default: () => panel.name })
        );
      if (panels.length > 2) {
        tags.push(
          h(NTag, { key: "remaining", size: "small" }, { default: () => `+${panels.length - 2}` })
        );
      }
      return h(NSpace, { size: 4, wrap: true }, { default: () => tags });
    }
  },
  {
    title: "Durum",
    key: "status",
    width: 175,
    sorter: (a, b) =>
      TECHNICAL_DOCUMENT_STATUSES.findIndex((status) => status.value === a.status) -
      TECHNICAL_DOCUMENT_STATUSES.findIndex((status) => status.value === b.status),
    render(document) {
      if (!props.canEdit) {
        return h(
          NTag,
          { size: "small", type: TECHNICAL_DOCUMENT_STATUS_TYPES[document.status] },
          { default: () => document.status_display }
        );
      }
      return h(NSelect, {
        class: "td-status-select",
        size: "small",
        value: document.status,
        options: TECHNICAL_DOCUMENT_STATUSES,
        "onUpdate:value": (value) => emit("update-status", document, value)
      });
    }
  },
  {
    title: "Rev.",
    key: "revision",
    width: 75,
    sorter: "default",
    render: (document) => h(NText, { strong: true }, { default: () => document.revision })
  },
  {
    title: "Yayın / termin",
    key: "dates",
    width: 170,
    sorter: (a, b) => (a.due_date || "9999").localeCompare(b.due_date || "9999"),
    render(document) {
      const overdue = props.isOverdue(document);
      return h(
        NSpace,
        { class: "td-date-stack", vertical: true, size: 2 },
        {
          default: () => [
            h(
              NText,
              { depth: 3 },
              {
                default: () => `Yayın · ${formatTechnicalDocumentDate(document.publication_date)}`
              }
            ),
            h(
              NText,
              { type: overdue ? "error" : "default", strong: overdue },
              { default: () => `Termin · ${formatTechnicalDocumentDate(document.due_date)}` }
            )
          ]
        }
      );
    }
  },
  {
    title: "Sorumlu",
    key: "owner_name",
    width: 190,
    sorter: (a, b) => (a.owner_name || "").localeCompare(b.owner_name || "", "tr"),
    render(document) {
      return h(NThing, {
        title: document.owner_name || "Atanmamış",
        description: document.last_notification_at
          ? `Son bildirim ${formatTechnicalDocumentDateTime(document.last_notification_at)}`
          : "Bildirim gönderilmedi"
      });
    }
  },
  {
    title: "İşlemler",
    key: "actions",
    width: props.canEdit ? 166 : 88,
    fixed: "right",
    align: "right",
    render(document) {
      const actions = [
        iconButton(Eye, "Detayı görüntüle", () => emit("open-detail", document)),
        iconButton(
          Mail,
          "Panel sorumlularına e-posta gönder",
          () => emit("open-notification", document),
          {
            type: "primary",
            disabled: !(document.notification_recipients || []).length,
            loading: props.notifyingId === document.id
          }
        )
      ];
      if (props.canEdit) {
        actions.push(
          iconButton(Pencil, "Dokümanı düzenle", () => emit("open-editor", document)),
          iconButton(Trash2, "Dokümanı sil", () => emit("request-delete", document), {
            type: "error"
          })
        );
      }
      return h(NSpace, { justify: "end", size: 2 }, { default: () => actions });
    }
  }
]);

const pagination = {
  pageSize: 10,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
  showQuickJumper: true
};
</script>

<template>
  <n-card class="td-table-card" content-style="padding: 0">
    <n-grid class="td-table-toolbar" cols="1 s:2 l:4" responsive="screen" :x-gap="10" :y-gap="10">
      <n-grid-item>
        <n-input
          v-model:value="filters.search"
          clearable
          placeholder="Kod, başlık, kapak veya sorumlu ara…"
        >
          <template #prefix
            ><n-icon><Search /></n-icon
          ></template>
        </n-input>
      </n-grid-item>
      <n-grid-item>
        <n-select
          v-model:value="filters.status"
          clearable
          placeholder="Tüm durumlar"
          :options="TECHNICAL_DOCUMENT_STATUSES"
        />
      </n-grid-item>
      <n-grid-item>
        <n-select
          v-model:value="filters.panelId"
          clearable
          placeholder="Tüm paneller"
          :options="panelOptions"
        />
      </n-grid-item>
      <n-grid-item>
        <n-select
          v-model:value="filters.category"
          clearable
          placeholder="Tüm kategoriler"
          :options="categoryOptions"
        />
      </n-grid-item>
    </n-grid>

    <n-flex class="td-table-summary" justify="space-between" align="center">
      <n-text strong>{{ documents.length }} doküman</n-text>
      <n-tag size="small" :bordered="false">{{ projectName }} proje kayıtları</n-tag>
    </n-flex>

    <n-data-table
      class="td-data-table"
      :columns="columns"
      :data="documents"
      :loading="loading"
      :pagination="pagination"
      :row-key="(document) => document.id"
      :scroll-x="1401"
      striped
    />
  </n-card>
</template>
