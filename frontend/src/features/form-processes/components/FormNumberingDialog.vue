<script setup>
defineProps({ controller: { type: Object, required: true } });
</script>

<template>
  <n-alert
    v-if="controller.pending.value"
    type="warning"
    title="Bekleyen numara işlemi"
    class="form-process-alert"
  >
    İşlem sonucu henüz doğrulanmadı. Yeni numara almadan önce mevcut işlemi kontrol edin.
    <n-button :loading="controller.busy.value" @click="controller.retry"
      >Kontrol et ve devam et</n-button
    >
  </n-alert>
  <n-alert v-if="controller.error.value" type="error" class="form-process-alert">{{
    controller.error.value
  }}</n-alert>
  <n-modal
    :show="Boolean(controller.selected.value) && !controller.pending.value"
    preset="card"
    title="Numara al"
    class="form-numbering-dialog"
    :mask-closable="!controller.busy.value"
    @update:show="!controller.busy.value && (controller.selected.value = null)"
  >
    <n-space vertical :size="16">
      <n-alert type="info" :show-icon="false"
        >Numara alındığında form kaydedilir. Numara ve kullanılan kaynak alanlar kilitlenir. Yeni
        form taslak olarak kaydedilir.</n-alert
      >
      <n-text strong>{{ controller.selected.value?.format_code }}</n-text>
      <n-form-item
        v-for="row in controller.contextRows.value"
        :key="row.key"
        :label="row.key"
        :required="row.source === 'manual'"
      >
        <n-input
          v-if="row.source === 'manual'"
          v-model:value="controller.manual.value[row.key]"
          :maxlength="row.max_length"
          show-count
          placeholder="Context değerini girin"
        />
        <n-text v-else>{{ row.value ?? "Format varsayılanı" }}</n-text>
      </n-form-item>
      <n-text v-if="!controller.contextRows.value.length" depth="3"
        >Bu format için context değeri gerekmiyor.</n-text
      >
      <n-space justify="end">
        <n-button :disabled="controller.busy.value" @click="controller.selected.value = null"
          >Vazgeç</n-button
        >
        <n-button type="primary" :loading="controller.busy.value" @click="controller.generate"
          >Numara al ve kaydet</n-button
        >
      </n-space>
    </n-space>
  </n-modal>
</template>
