<script setup>
import { computed } from "vue";

import { groupTemplateFields } from "../model/selectors";

const props = defineProps({
  form: { type: Object, required: true },
  template: { type: Object, required: true },
  record: { type: Object, default: null }
});

const groups = computed(() => groupTemplateFields(props.template.fields || []));

function displayValue(field) {
  const value = props.form.data[field.key];
  if (!value) return "—";
  if (field.type === "select") {
    return field.options?.find((option) => option.value === value)?.label || value;
  }
  return value;
}

function isEmptyRequired(field) {
  const value = props.form.data[field.key];
  if (field.type === "table") return field.required && (!Array.isArray(value) || !value.length);
  return field.required && !value;
}

function displayCell(column, value) {
  if (!value) return "—";
  if (column.type !== "date") return value;
  const [year, month, day] = value.split("-");
  return day && month && year ? `${day}.${month}.${year}` : value;
}
</script>

<template>
  <div class="form-process-review">
    <n-alert type="info" title="Form özeti">
      Bilgileri kontrol edin. “Tamamla” kaydı doğrudan onaylar; “İncele” adımı tek başına kayıt
      durumunu değiştirmez.
    </n-alert>
    <n-card size="small" title="Kayıt ve şablon">
      <n-descriptions label-placement="left" bordered :column="1">
        <n-descriptions-item label="Süreç">{{ template.process_name }}</n-descriptions-item>
        <n-descriptions-item label="FM şablonu">
          {{ template.form_number }} — {{ template.title }}
        </n-descriptions-item>
        <n-descriptions-item label="Kayıt numarası">{{ form.record_number }}</n-descriptions-item>
        <n-descriptions-item label="Kayıt başlığı">{{ form.title }}</n-descriptions-item>
        <n-descriptions-item v-if="record" label="Mevcut durum">
          {{ record.status_display }}
        </n-descriptions-item>
      </n-descriptions>
    </n-card>
    <n-card v-for="group in groups" :key="group.name" :title="group.name" size="small">
      <dl class="form-process-review-list">
        <template v-for="field in group.fields" :key="field.key">
          <dt>{{ field.label }}</dt>
          <dd :class="{ 'is-empty-required': isEmptyRequired(field) }">
            <div
              v-if="field.type === 'table' && form.data[field.key]?.length"
              class="form-process-review-table-wrap"
            >
              <table class="form-process-review-table">
                <thead>
                  <tr>
                    <th v-for="column in field.columns" :key="column.key">{{ column.label }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, rowIndex) in form.data[field.key]" :key="rowIndex">
                    <td v-for="column in field.columns" :key="column.key">
                      {{ displayCell(column, row[column.key]) }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <template v-else>{{ displayValue(field) }}</template>
          </dd>
        </template>
      </dl>
    </n-card>
    <n-card v-if="form.notes" title="Kayıt notları" size="small">
      <p class="form-process-review-notes">{{ form.notes }}</p>
    </n-card>
  </div>
</template>
