<script setup>
import { AlertTriangle, BellRing, CalendarClock, CheckCircle2, FileCheck2 } from "@lucide/vue";

defineProps({
  metrics: { type: Object, required: true },
  projectCode: { type: String, default: "" }
});
</script>

<template>
  <n-grid class="td-metric-grid" cols="1 s:2 m:3 l:5" responsive="screen" :x-gap="12" :y-gap="12">
    <n-grid-item>
      <n-card size="small" class="td-metric-card td-metric-card-primary">
        <n-statistic label="Toplam doküman" :value="metrics.total">
          <template #prefix
            ><n-icon><FileCheck2 /></n-icon
          ></template>
        </n-statistic>
        <n-text :depth="3">{{ projectCode }} kapsamı</n-text>
      </n-card>
    </n-grid-item>
    <n-grid-item>
      <n-card size="small" class="td-metric-card">
        <n-statistic label="Yayınlanan" :value="metrics.published">
          <template #prefix
            ><n-icon><CheckCircle2 /></n-icon
          ></template>
        </n-statistic>
        <n-progress
          type="line"
          status="success"
          :percentage="metrics.publicationRate"
          :height="5"
          :show-indicator="false"
        />
      </n-card>
    </n-grid-item>
    <n-grid-item>
      <n-card size="small" class="td-metric-card">
        <n-statistic label="Aktif iş akışı" :value="metrics.active">
          <template #prefix
            ><n-icon><CalendarClock /></n-icon
          ></template>
        </n-statistic>
        <n-text :depth="3">İnceleme ve onay</n-text>
      </n-card>
    </n-grid-item>
    <n-grid-item>
      <n-card
        size="small"
        class="td-metric-card"
        :class="{ 'td-metric-card-danger': metrics.overdue }"
      >
        <n-statistic label="Geciken" :value="metrics.overdue">
          <template #prefix
            ><n-icon><AlertTriangle /></n-icon
          ></template>
        </n-statistic>
        <n-text :type="metrics.overdue ? 'error' : 'default'" :depth="3">Termin aşımı</n-text>
      </n-card>
    </n-grid-item>
    <n-grid-item>
      <n-card size="small" class="td-metric-card">
        <n-statistic label="Bilgilendirilen" :value="metrics.notified">
          <template #prefix
            ><n-icon><BellRing /></n-icon
          ></template>
        </n-statistic>
        <n-text :depth="3">En az bir bildirim</n-text>
      </n-card>
    </n-grid-item>
  </n-grid>
</template>
