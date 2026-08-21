<script setup>
import { computed } from "vue";

const props = defineProps({
  summary: { type: Object, required: true },
  thresholds: { type: Object, required: true }
});

const cards = computed(() => [
  { key: "overdue", label: "Gecikmiş", tone: "danger" },
  {
    key: "next_7_days",
    label: `${props.thresholds.critical_days} gün içinde`,
    tone: "warning"
  },
  {
    key: "next_30_days",
    label: `${props.thresholds.horizon_days} gün içinde`,
    tone: "info"
  },
  { key: "stale", label: "Bekleyen iş akışı", tone: "neutral" }
]);
</script>

<template>
  <n-grid
    class="operational-summary-grid"
    cols="1 s:2 l:4"
    responsive="screen"
    :x-gap="12"
    :y-gap="12"
  >
    <n-grid-item v-for="card in cards" :key="card.key">
      <n-card size="small" class="operational-summary-card" :class="`is-${card.tone}`">
        <n-statistic :label="card.label" :value="summary[card.key] || 0" />
        <n-text v-if="card.key === 'stale'" depth="3">
          En az {{ thresholds.stale_days }} gündür bekliyor
        </n-text>
        <n-text v-else depth="3">Tarih bazlı operasyonel uyarı</n-text>
      </n-card>
    </n-grid-item>
  </n-grid>
</template>
