<script setup>
import {
  TECHNICAL_DOCUMENT_CLASSIFICATIONS,
  TECHNICAL_DOCUMENT_PRIORITIES,
  TECHNICAL_DOCUMENT_STATUSES
} from "../model/options";

defineProps({
  show: { type: Boolean, required: true },
  editingId: { type: Number, default: null },
  form: { type: Object, required: true },
  projects: { type: Array, required: true },
  panelOptions: { type: Array, required: true },
  formError: { type: String, default: "" },
  saving: { type: Boolean, required: true }
});

const emit = defineEmits(["update:show", "submit"]);
</script>

<template>
  <n-modal
    :show="show"
    preset="card"
    :title="editingId ? 'Teknik dokümanı düzenle' : 'Yeni teknik doküman'"
    class="td-editor-modal"
    @update:show="emit('update:show', $event)"
  >
    <n-form label-placement="top" @submit.prevent="emit('submit')">
      <n-grid cols="1 m:2" responsive="screen" item-responsive :x-gap="18">
        <n-grid-item>
          <n-form-item label="Proje" required>
            <n-select
              v-model:value="form.project"
              :disabled="Boolean(editingId)"
              :options="
                projects.map((project) => ({
                  label: `${project.code} — ${project.name}`,
                  value: project.id
                }))
              "
            />
          </n-form-item>
        </n-grid-item>
        <n-grid-item>
          <n-form-item label="İlgili paneller">
            <n-select
              v-model:value="form.panels"
              multiple
              clearable
              placeholder="Bir veya daha fazla panel seçin"
              :options="panelOptions"
            />
          </n-form-item>
        </n-grid-item>
        <n-grid-item>
          <n-form-item label="Doküman kodu" required>
            <n-input v-model:value="form.code" placeholder="TPL-SYS-001" />
          </n-form-item>
        </n-grid-item>
        <n-grid-item>
          <n-form-item label="Revizyon" required>
            <n-input v-model:value="form.revision" placeholder="A, B.1, 02…" />
          </n-form-item>
        </n-grid-item>
        <n-grid-item>
          <n-form-item label="Kapak sayfası numarası">
            <n-input v-model:value="form.cover_page_number" placeholder="KP-100" />
          </n-form-item>
        </n-grid-item>
        <n-grid-item>
          <n-form-item label="Kapak sayfası issue">
            <n-input v-model:value="form.cover_page_issue" placeholder="01, A, B.2…" />
          </n-form-item>
        </n-grid-item>
        <n-grid-item span="1 m:2">
          <n-form-item label="Başlık" required>
            <n-input v-model:value="form.title" placeholder="Dokümanın resmi başlığı" />
          </n-form-item>
        </n-grid-item>
        <n-grid-item>
          <n-form-item label="Kategori">
            <n-input v-model:value="form.category" placeholder="Sistem Mühendisliği" />
          </n-form-item>
        </n-grid-item>
        <n-grid-item>
          <n-form-item label="Doküman tipi">
            <n-input v-model:value="form.document_type" placeholder="Gereksinim, ICD, prosedür…" />
          </n-form-item>
        </n-grid-item>
        <n-grid-item>
          <n-form-item label="Durum">
            <n-select v-model:value="form.status" :options="TECHNICAL_DOCUMENT_STATUSES" />
          </n-form-item>
        </n-grid-item>
        <n-grid-item>
          <n-form-item label="Öncelik">
            <n-select v-model:value="form.priority" :options="TECHNICAL_DOCUMENT_PRIORITIES" />
          </n-form-item>
        </n-grid-item>
        <n-grid-item>
          <n-form-item label="Bilgi sınıfı">
            <n-select
              v-model:value="form.classification"
              :options="TECHNICAL_DOCUMENT_CLASSIFICATIONS"
            />
          </n-form-item>
        </n-grid-item>
        <n-grid-item>
          <n-form-item label="Doküman sorumlusu">
            <n-input v-model:value="form.owner_name" placeholder="Ekip veya kişi" />
          </n-form-item>
        </n-grid-item>
        <n-grid-item>
          <n-form-item label="Yayın tarihi">
            <n-date-picker
              v-model:formatted-value="form.publication_date"
              type="date"
              value-format="yyyy-MM-dd"
              clearable
            />
          </n-form-item>
        </n-grid-item>
        <n-grid-item>
          <n-form-item label="Termin">
            <n-date-picker
              v-model:formatted-value="form.due_date"
              type="date"
              value-format="yyyy-MM-dd"
              clearable
            />
          </n-form-item>
        </n-grid-item>
        <n-grid-item>
          <n-form-item label="Sonraki gözden geçirme">
            <n-date-picker
              v-model:formatted-value="form.review_date"
              type="date"
              value-format="yyyy-MM-dd"
              clearable
            />
          </n-form-item>
        </n-grid-item>
        <n-grid-item>
          <n-form-item label="Kaynak bağlantısı">
            <n-input v-model:value="form.source_url" placeholder="https://…" />
          </n-form-item>
        </n-grid-item>
        <n-grid-item span="1 m:2">
          <n-form-item label="Açıklama">
            <n-input v-model:value="form.description" type="textarea" :rows="3" />
          </n-form-item>
        </n-grid-item>
        <n-grid-item span="1 m:2">
          <n-form-item label="Notlar">
            <n-input v-model:value="form.notes" type="textarea" :rows="2" />
          </n-form-item>
        </n-grid-item>
      </n-grid>
      <n-alert v-if="formError" type="error" :show-icon="true">{{ formError }}</n-alert>
      <n-divider />
      <n-flex justify="end">
        <n-button @click="emit('update:show', false)">Vazgeç</n-button>
        <n-button attr-type="submit" type="primary" :loading="saving">
          {{ editingId ? "Değişiklikleri kaydet" : "Dokümanı oluştur" }}
        </n-button>
      </n-flex>
    </n-form>
  </n-modal>
</template>
