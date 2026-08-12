<script setup>
import { ExternalLink, Paperclip } from "@lucide/vue";

import { formatFlightPermitFileSize } from "../model/formatters";
import { FLIGHT_PERMIT_RECORD_STATUSES, FLIGHT_PURPOSE_OPTIONS } from "../model/options";
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
      <n-flex justify="space-between" align="center" class="fp-form-section">
        <n-text strong>İzin bilgileri</n-text>
        <n-flex align="center" :size="8">
          <n-text>Uçuş izni tavsiyesi</n-text>
          <n-switch v-model:value="form.is_recommendation" aria-label="Uçuş izni tavsiyesi" />
        </n-flex>
      </n-flex>
      <n-grid cols="1 s:2" responsive="screen" :x-gap="16">
        <n-form-item-gi label="Başvuru sahibi" required>
          <n-input
            v-model:value="form.permit_applicant"
            placeholder="TÜRK HAVACILIK VE UZAY SANAYİ A.Ş. (TUSAŞ)"
          />
        </n-form-item-gi>
        <n-form-item-gi label="Uçuş izin numarası" required>
          <n-input v-model:value="form.permit_number" placeholder="Örn. SHGM-UI-2026-0042" />
        </n-form-item-gi>
        <n-form-item-gi label="Kayıt durumu" required>
          <n-select v-model:value="form.status" :options="FLIGHT_PERMIT_RECORD_STATUSES" />
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

      <n-divider>Hava aracı</n-divider>
      <n-grid cols="1 s:2" responsive="screen" :x-gap="16">
        <n-form-item-gi label="Uyruğu">
          <n-input
            v-model:value="form.aircraft_nationality"
            placeholder="Tail Number: XX-XXX / Serial Number: XXXXX"
          />
        </n-form-item-gi>
        <n-form-item-gi label="Kayıt tanımlaması">
          <n-input v-model:value="form.aircraft_id_mark" placeholder="Örn. TC-UAV-104" />
        </n-form-item-gi>
        <n-form-item-gi label="Hava aracı sahibi">
          <n-input v-model:value="form.aircraft_owner" placeholder="Devlet Malı Uçağı (DMU)" />
        </n-form-item-gi>
        <n-form-item-gi label="Seri numarası">
          <n-input v-model:value="form.serial_number" placeholder="Serial Number: XXXXX" />
        </n-form-item-gi>
        <n-form-item-gi label="Üretici">
          <n-input v-model:value="form.aircraft_manufacturer" placeholder="Boeing" />
        </n-form-item-gi>
        <n-form-item-gi label="Hava aracı tipi">
          <n-input v-model:value="form.aircraft_type" placeholder="737-700" />
        </n-form-item-gi>
      </n-grid>

      <n-divider>Uçuş kapsamı ve koşulları</n-divider>
      <n-grid cols="1 s:2" responsive="screen" :x-gap="16">
        <n-form-item-gi label="Hedef uçuş tarihi">
          <n-date-picker
            v-model:formatted-value="form.target_date"
            value-format="yyyy-MM-dd"
            type="date"
            clearable
          />
        </n-form-item-gi>
        <n-form-item-gi label="Öngörülen uçuş süresi (saat)">
          <n-input-number v-model:value="form.flight_duration" :min="1" clearable />
        </n-form-item-gi>
      </n-grid>

      <n-form-item label="Uçuşun amacı">
        <n-checkbox-group v-model:value="form.purpose_of_flight" class="fp-purpose-options">
          <n-checkbox
            v-for="option in FLIGHT_PURPOSE_OPTIONS"
            :key="option.value"
            :value="option.value"
            :label="option.label"
          />
        </n-checkbox-group>
      </n-form-item>
      <n-form-item label="Uçuş izniyle ilgili hava aracı konfigürasyonu">
        <n-input v-model:value="form.aircraft_configuration" type="textarea" :rows="2" />
      </n-form-item>
      <n-form-item label="Koşullar ve kısıtlamalar">
        <n-input v-model:value="form.conditions_restrictions" type="textarea" :rows="2" />
      </n-form-item>
      <n-form-item label="Uçuş koşullarıyla ilgili kanıtlar">
        <n-input v-model:value="form.conditions_substantiations" type="textarea" :rows="2" />
      </n-form-item>

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
