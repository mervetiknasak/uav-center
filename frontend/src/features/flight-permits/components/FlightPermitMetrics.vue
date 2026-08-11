<script setup>
import { AlertTriangle, CalendarDays, FileCheck2, Paperclip, ShieldCheck } from "@lucide/vue";

defineProps({ metrics: { type: Object, required: true } });
</script>

<template>
  <n-grid cols="1 s:2 m:3 l:5" responsive="screen" :x-gap="12" :y-gap="12">
    <n-grid-item>
      <n-card size="small" class="fp-metric fp-metric-primary">
        <n-statistic label="Toplam izin" :value="metrics.total">
          <template #prefix
            ><n-icon><FileCheck2 /></n-icon
          ></template>
        </n-statistic>
        <n-text :depth="3">Tüm uçaklar</n-text>
      </n-card>
    </n-grid-item>
    <n-grid-item>
      <n-card size="small" class="fp-metric">
        <n-statistic label="Geçerli" :value="metrics.active">
          <template #prefix
            ><n-icon><ShieldCheck /></n-icon
          ></template>
        </n-statistic>
        <n-text :depth="3">30 günden uzun</n-text>
      </n-card>
    </n-grid-item>
    <n-grid-item>
      <n-card size="small" class="fp-metric fp-metric-warning">
        <n-statistic label="Süresi yaklaşan" :value="metrics.expiring">
          <template #prefix
            ><n-icon><CalendarDays /></n-icon
          ></template>
        </n-statistic>
        <n-text :depth="3">Son 30 gün</n-text>
      </n-card>
    </n-grid-item>
    <n-grid-item>
      <n-card size="small" class="fp-metric fp-metric-danger">
        <n-statistic label="Süresi dolan" :value="metrics.expired">
          <template #prefix
            ><n-icon><AlertTriangle /></n-icon
          ></template>
        </n-statistic>
        <n-text :depth="3">Yenileme gerekli</n-text>
      </n-card>
    </n-grid-item>
    <n-grid-item>
      <n-card size="small" class="fp-metric">
        <n-statistic label="Dokümanlı" :value="metrics.documented">
          <template #prefix
            ><n-icon><Paperclip /></n-icon
          ></template>
        </n-statistic>
        <n-text :depth="3">Dosyası ekli</n-text>
      </n-card>
    </n-grid-item>
  </n-grid>
</template>
