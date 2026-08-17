<script setup>
const props = defineProps({
  field: { type: Object, required: true },
  value: { type: Array, default: () => [] }
});

const emit = defineEmits(["update:value"]);

function emptyRow() {
  return Object.fromEntries(
    (props.field.columns || []).map((column) => [column.key, column.type === "date" ? null : ""])
  );
}

function addRow() {
  if (props.value.length >= props.field.max_items) return;
  emit("update:value", [...props.value, emptyRow()]);
}

function updateCell(rowIndex, columnKey, value) {
  const rows = props.value.map((row, index) =>
    index === rowIndex ? { ...row, [columnKey]: value } : row
  );
  emit("update:value", rows);
}

function removeRow(rowIndex) {
  emit(
    "update:value",
    props.value.filter((_, index) => index !== rowIndex)
  );
}
</script>

<template>
  <div :id="`fm-field-${field.key}`" class="form-process-table-field" tabindex="-1">
    <div v-if="value.length" class="form-process-table-field-scroll">
      <table>
        <thead>
          <tr>
            <th v-for="column in field.columns" :key="column.key">
              {{ column.label }}<span v-if="column.required" aria-hidden="true"> *</span>
            </th>
            <th><span class="sr-only">Satır işlemleri</span></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, rowIndex) in value" :key="rowIndex">
            <td v-for="column in field.columns" :key="column.key">
              <n-date-picker
                v-if="column.type === 'date'"
                :formatted-value="row[column.key] || null"
                value-format="yyyy-MM-dd"
                type="date"
                clearable
                :aria-label="`${rowIndex + 1}. satır ${column.label}`"
                @update:formatted-value="updateCell(rowIndex, column.key, $event)"
              />
              <n-input
                v-else
                :value="row[column.key] || ''"
                :maxlength="column.max_length"
                :aria-label="`${rowIndex + 1}. satır ${column.label}`"
                @update:value="updateCell(rowIndex, column.key, $event)"
              />
            </td>
            <td class="form-process-table-row-actions">
              <n-button
                tertiary
                type="error"
                :aria-label="`${rowIndex + 1}. satırı kaldır`"
                @click="removeRow(rowIndex)"
              >
                Kaldır
              </n-button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <n-empty v-else size="small" description="Henüz satır eklenmedi" />
    <n-button secondary type="primary" :disabled="value.length >= field.max_items" @click="addRow">
      Satır ekle
    </n-button>
    <small>En fazla {{ field.max_items }} satır eklenebilir.</small>
  </div>
</template>
