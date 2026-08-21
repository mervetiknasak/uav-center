<script setup>
import { computed, h } from "vue";
import { ExternalLink, Mail } from "@lucide/vue";
import { NButton, NIcon, NSpace, NTag, NText } from "naive-ui";

import {
  formatOperationalAlertDate,
  OPERATIONAL_ALERT_BUCKET_LABELS,
  OPERATIONAL_ALERT_BUCKET_TYPES,
  OPERATIONAL_ALERT_SOURCE_LABELS,
  OPERATIONAL_ALERT_TYPE_LABELS,
  operationalAlertTimingLabel
} from "../model/alerts";

defineProps({
  alerts: { type: Array, required: true },
  loading: { type: Boolean, required: true },
  emptyDescription: { type: String, required: true }
});

const emit = defineEmits(["open", "notify"]);

const priorityLabels = {
  low: "Düşük",
  normal: "Normal",
  high: "Yüksek",
  critical: "Kritik"
};

const priorityTypes = {
  low: "default",
  normal: "info",
  high: "warning",
  critical: "error"
};

const columns = computed(() => [
  {
    title: "Kayıt",
    key: "record",
    minWidth: 265,
    fixed: "left",
    render(alert) {
      return h(
        NSpace,
        { vertical: true, size: 3 },
        {
          default: () => [
            h(
              NSpace,
              { size: 6, align: "center" },
              {
                default: () => [
                  h(
                    NTag,
                    { size: "small", bordered: false },
                    { default: () => OPERATIONAL_ALERT_SOURCE_LABELS[alert.source_type] }
                  ),
                  h(NText, { strong: true, type: "primary" }, { default: () => alert.reference })
                ]
              }
            ),
            h(NText, null, { default: () => alert.title })
          ]
        }
      );
    }
  },
  {
    title: "Uyarı",
    key: "alert_type",
    width: 180,
    render(alert) {
      return h(
        NSpace,
        { vertical: true, size: 4 },
        {
          default: () => [
            h(
              NText,
              { strong: true },
              { default: () => OPERATIONAL_ALERT_TYPE_LABELS[alert.alert_type] }
            ),
            h(
              NTag,
              {
                size: "small",
                bordered: false,
                type: OPERATIONAL_ALERT_BUCKET_TYPES[alert.bucket]
              },
              { default: () => OPERATIONAL_ALERT_BUCKET_LABELS[alert.bucket] }
            )
          ]
        }
      );
    }
  },
  {
    title: "Tarih / süre",
    key: "date",
    width: 175,
    render(alert) {
      return h(
        NSpace,
        { vertical: true, size: 2 },
        {
          default: () => [
            h(
              NText,
              { strong: Boolean(alert.date) },
              { default: () => formatOperationalAlertDate(alert.date) }
            ),
            h(
              NText,
              {
                type: alert.bucket === "overdue" ? "error" : "default",
                depth: alert.bucket === "overdue" ? undefined : 3
              },
              { default: () => operationalAlertTimingLabel(alert) }
            )
          ]
        }
      );
    }
  },
  {
    title: "Proje / panel",
    key: "project",
    minWidth: 220,
    render(alert) {
      const panelNames = (alert.panels || []).map((panel) => panel.name).join(", ");
      return h(
        NSpace,
        { vertical: true, size: 2 },
        {
          default: () => [
            h(
              NText,
              { strong: Boolean(alert.project) },
              {
                default: () =>
                  alert.project
                    ? `${alert.project.code} — ${alert.project.name}`
                    : "Proje kapsamı yok"
              }
            ),
            h(NText, { depth: 3 }, { default: () => panelNames || "Panel kapsamı yok" })
          ]
        }
      );
    }
  },
  {
    title: "Durum / öncelik",
    key: "status",
    width: 165,
    render(alert) {
      return h(
        NSpace,
        { vertical: true, size: 4, align: "start" },
        {
          default: () =>
            [
              h(NTag, { size: "small", bordered: false }, { default: () => alert.status_display }),
              alert.priority
                ? h(
                    NTag,
                    { size: "small", type: priorityTypes[alert.priority] },
                    { default: () => priorityLabels[alert.priority] || alert.priority }
                  )
                : null
            ].filter(Boolean)
        }
      );
    }
  },
  {
    title: "İşlemler",
    key: "actions",
    width: 230,
    fixed: "right",
    align: "right",
    render(alert) {
      const actions = [
        h(
          NButton,
          { size: "small", secondary: true, type: "primary", onClick: () => emit("open", alert) },
          {
            icon: () => h(NIcon, null, { default: () => h(ExternalLink, { size: 16 }) }),
            default: () => "Kayda git"
          }
        )
      ];
      if (alert.can_notify) {
        actions.push(
          h(
            NButton,
            { size: "small", tertiary: true, onClick: () => emit("notify", alert) },
            {
              icon: () => h(NIcon, null, { default: () => h(Mail, { size: 16 }) }),
              default: () => "Bildirim hazırla"
            }
          )
        );
      }
      return h(NSpace, { justify: "end", size: 6 }, { default: () => actions });
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
  <n-data-table
    class="operational-alerts-data-table"
    :columns="columns"
    :data="alerts"
    :loading="loading"
    :pagination="pagination"
    :row-key="(alert) => alert.key"
    :scroll-x="1235"
    striped
  >
    <template #empty>
      <n-empty :description="emptyDescription" />
    </template>
  </n-data-table>
</template>
