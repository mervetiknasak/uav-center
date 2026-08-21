<script setup>
import { computed, reactive, watch } from "vue";
import { CalendarClock, RefreshCw, Search } from "@lucide/vue";

import {
  filterOperationalAlerts,
  formatOperationalAlertDate,
  OPERATIONAL_ALERT_BUCKETS,
  OPERATIONAL_ALERT_SOURCES,
  selectOperationalAlertPanels,
  selectOperationalAlertProjects,
  sortOperationalAlerts
} from "../model/alerts";
import OperationalAlertSummary from "./OperationalAlertSummary.vue";
import OperationalAlertsTable from "./OperationalAlertsTable.vue";

const props = defineProps({
  data: { type: Object, required: true },
  loading: { type: Boolean, required: true },
  error: { type: String, default: "" }
});

const emit = defineEmits(["refresh", "open", "notify"]);
const filters = reactive({
  search: "",
  sourceType: null,
  bucket: null,
  projectId: null,
  panelId: null
});

const projectOptions = computed(() => selectOperationalAlertProjects(props.data.alerts));
const panelOptions = computed(() =>
  selectOperationalAlertPanels(props.data.alerts, filters.projectId)
);
const filteredAlerts = computed(() =>
  sortOperationalAlerts(filterOperationalAlerts(props.data.alerts, filters))
);
const emptyDescription = computed(() => {
  if (props.loading) return "Operasyonel uyarılar yükleniyor…";
  if (props.error) return "Uyarılar yüklenemedi. Yenileyerek tekrar deneyin.";
  return props.data.alerts.length
    ? "Bu filtrelerle eşleşen operasyonel uyarı bulunamadı."
    : "Şu anda takip edilmesi gereken operasyonel uyarı bulunmuyor.";
});

watch(panelOptions, (options) => {
  if (!options.some((option) => option.value === filters.panelId)) {
    filters.panelId = null;
  }
});
</script>

<template>
  <section class="operational-calendar-view">
    <n-page-header
      title="Operasyonel Takvim"
      subtitle="Terminleri, incelemeleri, bekleyen iş akışlarını ve uçuş izni geçerliliklerini tek merkezden izleyin."
    >
      <template #header>
        <n-space align="center" :size="6">
          <n-icon :size="16"><CalendarClock /></n-icon>
          <n-text type="primary" strong>İşlemler</n-text>
        </n-space>
      </template>
      <template #extra>
        <n-space align="center">
          <n-tag v-if="data.as_of" size="small" :bordered="false">
            {{ formatOperationalAlertDate(data.as_of) }} itibarıyla
          </n-tag>
          <n-button secondary :loading="loading" @click="emit('refresh')">
            <template #icon
              ><n-icon><RefreshCw /></n-icon
            ></template>
            Yenile
          </n-button>
        </n-space>
      </template>
    </n-page-header>

    <n-alert v-if="error" type="error" title="Operasyonel uyarılar alınamadı">
      {{ error }}
    </n-alert>

    <OperationalAlertSummary :summary="data.summary" :thresholds="data.thresholds" />

    <n-card class="operational-alerts-card" content-style="padding: 0">
      <n-grid
        class="operational-alert-filters"
        cols="1 s:2 l:5"
        responsive="screen"
        :x-gap="10"
        :y-gap="10"
      >
        <n-grid-item>
          <n-input
            v-model:value="filters.search"
            aria-label="Operasyonel uyarılarda ara"
            clearable
            placeholder="Kayıt veya proje ara…"
          >
            <template #prefix
              ><n-icon><Search /></n-icon
            ></template>
          </n-input>
        </n-grid-item>
        <n-grid-item>
          <n-select
            v-model:value="filters.sourceType"
            aria-label="Uyarı kaynağı filtresi"
            :options="OPERATIONAL_ALERT_SOURCES"
            clearable
            placeholder="Tüm kaynaklar"
          />
        </n-grid-item>
        <n-grid-item>
          <n-select
            v-model:value="filters.bucket"
            aria-label="Uyarı aciliyeti filtresi"
            :options="OPERATIONAL_ALERT_BUCKETS"
            clearable
            placeholder="Tüm aciliyetler"
          />
        </n-grid-item>
        <n-grid-item>
          <n-select
            v-model:value="filters.projectId"
            aria-label="Proje filtresi"
            :options="projectOptions"
            clearable
            filterable
            placeholder="Tüm projeler"
          />
        </n-grid-item>
        <n-grid-item>
          <n-select
            v-model:value="filters.panelId"
            aria-label="Panel filtresi"
            :options="panelOptions"
            :disabled="!panelOptions.length"
            clearable
            filterable
            placeholder="Tüm paneller"
          />
        </n-grid-item>
      </n-grid>

      <n-flex class="operational-alerts-summary" justify="space-between" align="center">
        <n-text strong>{{ filteredAlerts.length }} uyarı gösteriliyor</n-text>
        <n-tag size="small" :bordered="false">Toplam {{ data.summary.total }}</n-tag>
      </n-flex>

      <n-spin :show="loading">
        <OperationalAlertsTable
          :alerts="filteredAlerts"
          :loading="loading"
          :empty-description="emptyDescription"
          @open="emit('open', $event)"
          @notify="emit('notify', $event)"
        />
      </n-spin>
    </n-card>
  </section>
</template>
