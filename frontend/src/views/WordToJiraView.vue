<script setup>
import { ref } from "vue";

const emit = defineEmits(["parse"]);

defineProps({
  loading: Boolean,
  error: {
    type: String,
    default: ""
  },
  result: {
    type: Object,
    default: null
  }
});

const selectedFileName = ref("");

const actionItemColumns = [
  { title: "No", key: "no", width: 80 },
  { title: "Aksiyon Maddesi", key: "action_item", minWidth: 320 },
  { title: "Sorumlu", key: "responsible", minWidth: 180 },
  { title: "Termin Tarihi", key: "due_date", width: 150 }
];

const cellColumns = [
  { title: "Index", key: "index", width: 80 },
  { title: "Tablo", key: "table_index", width: 80 },
  { title: "Satır", key: "row_index", width: 80 },
  { title: "Sütun", key: "column_index", width: 80 },
  { title: "Hücre İçeriği", key: "text", minWidth: 360 }
];

function parseFile({ file, onFinish, onError }) {
  selectedFileName.value = file.name;
  emit("parse", { file: file.file, onFinish, onError });
}
</script>

<template>
  <section class="word-jira-view">
    <div class="page-heading">
      <p>Araçlar</p>
      <h1>Toplantı Tutanağı Okuyucu</h1>
      <span>Word formatındaki toplantı tutanağını yükleyin; toplantı bilgilerini, kararları ve aksiyon maddelerini otomatik olarak çıkarın.</span>
    </div>

    <n-card title="Toplantı Tutanağı Yükle" size="small">
      <n-space vertical :size="16">
        <n-upload
          directory-dnd
          :max="1"
          accept=".docx"
          :custom-request="parseFile"
          :disabled="loading"
        >
          <n-upload-dragger>
            <div class="upload-title">Toplantı tutanağını buraya bırakın</div>
            <div class="upload-subtitle">
              {{ selectedFileName || "Desteklenen dosya biçimi: .docx" }}
            </div>
          </n-upload-dragger>
        </n-upload>

        <n-alert v-if="error" type="error" title="Tutanak okunamadı">{{ error }}</n-alert>
      </n-space>
    </n-card>

    <n-card v-if="result" title="Tutanak Özeti" size="small">
      <n-space vertical :size="14">
        <n-card title="Toplantı Bilgileri" size="small" embedded>
          <n-descriptions
            :column="1"
            label-placement="left"
            bordered
            size="small"
          >
            <n-descriptions-item label="Proje">
              {{ result.extracted_data?.project || "Bulunamadı" }}
            </n-descriptions-item>
            <n-descriptions-item label="Konu">
              {{ result.extracted_data?.subject || "Bulunamadı" }}
            </n-descriptions-item>
            <n-descriptions-item label="Tutanak No">
              {{ result.extracted_data?.mom_no || "Bulunamadı" }}
            </n-descriptions-item>
            <n-descriptions-item label="Revizyon">
              {{ result.extracted_data?.revision || "Bulunamadı" }}
            </n-descriptions-item>
            <n-descriptions-item label="Tarih / Saat">
              {{ result.extracted_data?.date_time || "Bulunamadı" }}
            </n-descriptions-item>
            <n-descriptions-item label="Toplantı Yeri">
              {{ result.extracted_data?.location || "Bulunamadı" }}
            </n-descriptions-item>
            <n-descriptions-item label="Gündem">
              {{ result.extracted_data?.agenda || "Bulunamadı" }}
            </n-descriptions-item>
            <n-descriptions-item label="Görüşmeler ve Kararlar">
              <span class="word-multiline-text">
                {{ result.extracted_data?.discussions_decisions || "Bulunamadı" }}
              </span>
            </n-descriptions-item>
          </n-descriptions>

          <div class="word-action-items">
            <strong>Aksiyon Maddeleri</strong>
            <n-alert
              v-if="!result.extracted_data?.action_item_list_found || !result.extracted_data?.attachments_found"
              type="warning"
              title="Aksiyon listesi bulunamadı"
            >
              Tutanaktaki aksiyon listesi veya ekler bölümü tanımlanamadı.
            </n-alert>
            <div
              v-else-if="result.extracted_data.action_items.length"
              class="word-cell-table-wrap"
            >
              <n-data-table
                :columns="actionItemColumns"
                :data="result.extracted_data.action_items"
                :row-key="(row) => `${row.no}-${row.action_item}`"
                :scroll-x="730"
                size="small"
                striped
              />
            </div>
            <n-empty v-else description="Tutanakta aksiyon maddesi bulunamadı" />
          </div>
        </n-card>

        <n-descriptions :column="3" bordered size="small">
          <n-descriptions-item label="Kaynak Dosya">{{ result.file_name }}</n-descriptions-item>
          <n-descriptions-item label="Okunan Tablo">{{ result.table_count }}</n-descriptions-item>
          <n-descriptions-item label="İşlenen Alan">{{ result.cell_count }}</n-descriptions-item>
        </n-descriptions>

        <n-collapse>
          <n-collapse-item
            title="Teknik Okuma Detaylarını Görüntüle"
            name="word-cell-details"
          >
            <n-data-table
              class="word-index-table"
              :columns="cellColumns"
              :data="result.cells"
              :row-key="(row) => row.index"
              :max-height="560"
              :scroll-x="680"
              size="small"
              striped
              virtual-scroll
            />
          </n-collapse-item>
        </n-collapse>
      </n-space>
    </n-card>
  </section>
</template>
