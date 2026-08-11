<script setup>
import { ExternalLink, Paperclip } from "@lucide/vue";

import { formatFlightPermitFileSize } from "../model/formatters";
import { FLIGHT_PERMIT_RECORD_STATUSES, FLIGHT_PERMIT_TYPES } from "../model/options";
import { FLIGHT_PERMIT_FILE_ACCEPT } from "../model/validation";

defineProps({
  show: { type: Boolean, required: true },
  editingId: { type: Number, default: null },
  form: { type: Object, required: true },
  formError: { type: String, default: "" },
  fileList: { type: Array, required: true },
  existingDocument: { type: Object, default: null },
  saving: { type: Boolean, required: true }
});

const emit = defineEmits([
  "update:show",
  "submit",
  "open-document",
  "remove-document",
  "update:file-list"
]);
</script>

<template>
  <n-modal
    :show="show"
    preset="card"
    class="fp-editor-modal"
    :title="editingId ? 'Uçuş iznini düzenle' : 'Yeni uçuş izni'"
    :bordered="false"
    @update:show="emit('update:show', $event)"
  >
    <n-alert v-if="formError" type="error" class="fp-form-alert">{{ formError }}</n-alert>
    <n-form label-placement="top">
      <n-grid cols="1 s:2" responsive="screen" :x-gap="16">
        <n-form-item-gi label="Uçak numarası" required>
          <n-input v-model:value="form.aircraft_number" placeholder="Örn. TC-UAV-104" />
        </n-form-item-gi>
        <n-form-item-gi label="Uçuş izin numarası" required>
          <n-input v-model:value="form.permit_number" placeholder="Örn. SHGM-UI-2026-0042" />
        </n-form-item-gi>
        <n-form-item-gi label="İzin türü" required>
          <n-select v-model:value="form.permit_type" :options="FLIGHT_PERMIT_TYPES" />
        </n-form-item-gi>
        <n-form-item-gi label="Kayıt durumu" required>
          <n-select v-model:value="form.status" :options="FLIGHT_PERMIT_RECORD_STATUSES" />
        </n-form-item-gi>
        <n-form-item-gi label="İzni veren kurum" required>
          <n-input v-model:value="form.issuing_authority" placeholder="Örn. SHGM" />
        </n-form-item-gi>
        <n-form-item-gi label="Uçuş bölgesi / kapsam">
          <n-input
            v-model:value="form.flight_region"
            placeholder="Örn. Ankara FIR / Test Sahası A"
          />
        </n-form-item-gi>
        <n-form-item-gi label="Geçerlilik başlangıcı" required>
          <n-date-picker
            v-model:formatted-value="form.valid_from"
            value-format="yyyy-MM-dd"
            type="date"
            clearable
          />
        </n-form-item-gi>
        <n-form-item-gi label="Geçerlilik bitişi" required>
          <n-date-picker
            v-model:formatted-value="form.valid_until"
            value-format="yyyy-MM-dd"
            type="date"
            clearable
          />
        </n-form-item-gi>
      </n-grid>

      <n-form-item label="Notlar">
        <n-input
          v-model:value="form.notes"
          type="textarea"
          :rows="3"
          placeholder="Operasyon koşulları veya ek açıklamalar…"
        />
      </n-form-item>

      <n-form-item label="İzin dokümanı">
        <div class="fp-upload-area">
          <n-alert v-if="existingDocument" type="info" :show-icon="false">
            <n-flex justify="space-between" align="center">
              <n-button text type="primary" @click="emit('open-document', existingDocument.url)">
                <template #icon
                  ><n-icon><ExternalLink /></n-icon
                ></template>
                {{ existingDocument.name }} ·
                {{ formatFlightPermitFileSize(existingDocument.size) }}
              </n-button>
              <n-button text type="error" @click="emit('remove-document')">Kaldır</n-button>
            </n-flex>
          </n-alert>
          <n-upload
            :file-list="fileList"
            :default-upload="false"
            :max="1"
            :accept="FLIGHT_PERMIT_FILE_ACCEPT"
            @update:file-list="emit('update:file-list', $event)"
          >
            <n-upload-dragger>
              <n-icon :size="32" :depth="3"><Paperclip /></n-icon>
              <n-text class="fp-upload-title">Dokümanı buraya bırakın veya seçin</n-text>
              <n-text :depth="3">PDF, DOCX, XLSX veya görsel · en fazla 15 MB</n-text>
            </n-upload-dragger>
          </n-upload>
        </div>
      </n-form-item>
    </n-form>
    <template #footer>
      <n-flex justify="end">
        <n-button @click="emit('update:show', false)">Vazgeç</n-button>
        <n-button type="primary" :loading="saving" @click="emit('submit')">Kaydet</n-button>
      </n-flex>
    </template>
  </n-modal>
</template>
