<script setup>
import { Mail } from "@lucide/vue";

import { formatTechnicalDocumentDate, formatTechnicalDocumentDateTime } from "../model/formatters";
import { TECHNICAL_DOCUMENT_STATUS_TYPES } from "../model/options";

defineProps({
  show: { type: Boolean, required: true },
  document: { type: Object, default: null }
});

const emit = defineEmits(["update:show"]);
</script>

<template>
  <n-drawer :show="show" :width="620" @update:show="emit('update:show', $event)">
    <n-drawer-content v-if="document" :title="document.code" closable>
      <n-thing
        class="td-detail-heading"
        :title="document.title"
        :description="document.description || 'Açıklama girilmemiş.'"
      >
        <template #header-extra>
          <n-space>
            <n-tag :type="TECHNICAL_DOCUMENT_STATUS_TYPES[document.status]">
              {{ document.status_display }}
            </n-tag>
            <n-tag :bordered="false">Rev. {{ document.revision }}</n-tag>
          </n-space>
        </template>
      </n-thing>
      <n-descriptions :column="2" bordered label-placement="top">
        <n-descriptions-item label="Proje">{{ document.project_name }}</n-descriptions-item>
        <n-descriptions-item label="Sorumlu">{{ document.owner_name || "—" }}</n-descriptions-item>
        <n-descriptions-item label="Kategori">{{ document.category || "—" }}</n-descriptions-item>
        <n-descriptions-item label="Tip">{{ document.document_type || "—" }}</n-descriptions-item>
        <n-descriptions-item label="Kapak sayfası">
          {{ document.cover_page?.number || "—" }}
        </n-descriptions-item>
        <n-descriptions-item label="Kapak revizyonu">
          {{ document.cover_page?.issue || "—" }}
        </n-descriptions-item>
        <n-descriptions-item label="Yayın tarihi">
          {{ formatTechnicalDocumentDate(document.publication_date) }}
        </n-descriptions-item>
        <n-descriptions-item label="Termin">
          {{ formatTechnicalDocumentDate(document.due_date) }}
        </n-descriptions-item>
        <n-descriptions-item label="Bilgi sınıfı">
          {{ document.classification_display }}
        </n-descriptions-item>
        <n-descriptions-item label="Son güncelleme">
          {{ formatTechnicalDocumentDateTime(document.updated_at) }}
        </n-descriptions-item>
      </n-descriptions>

      <n-divider title-placement="left">
        <n-space align="center">
          <n-text strong>Panel kapsamı</n-text>
          <n-badge :value="(document.panel_details || []).length" />
        </n-space>
      </n-divider>
      <section>
        <n-space v-if="(document.panel_details || []).length">
          <n-tag v-for="panel in document.panel_details" :key="panel.id">
            {{ panel.name }} · {{ panel.responsible_count }} sorumlu
          </n-tag>
        </n-space>
        <n-text v-else :depth="3">Bu doküman proje genelini kapsıyor.</n-text>
      </section>

      <n-divider title-placement="left">
        <n-space align="center">
          <n-text strong>Durum geçmişi</n-text>
          <n-badge :value="(document.status_history || []).length" />
        </n-space>
      </n-divider>
      <section>
        <n-timeline v-if="(document.status_history || []).length">
          <n-timeline-item
            v-for="history in document.status_history"
            :key="history.id"
            :type="history.to_status === 'published' ? 'success' : 'info'"
            :title="history.to_status_display"
            :content="history.note || 'Durum güncellendi.'"
            :time="`${formatTechnicalDocumentDateTime(history.created_at)} · ${history.changed_by_name || 'Sistem'}`"
          />
        </n-timeline>
        <n-text v-else :depth="3">Durum hareketi bulunmuyor.</n-text>
      </section>

      <n-divider title-placement="left">
        <n-space align="center">
          <n-text strong>Bildirim geçmişi</n-text>
          <n-badge :value="(document.notifications || []).length" />
        </n-space>
      </n-divider>
      <section>
        <n-list v-if="(document.notifications || []).length" bordered>
          <n-list-item v-for="notification in document.notifications" :key="notification.id">
            <template #prefix
              ><n-icon><Mail /></n-icon
            ></template>
            <n-thing
              :title="notification.subject"
              :description="`${notification.recipient_count} alıcı · ${formatTechnicalDocumentDateTime(notification.created_at)}`"
            />
            <template #suffix>
              <n-tag size="small" :type="notification.status === 'sent' ? 'success' : 'error'">
                {{ notification.status === "sent" ? "Gönderildi" : "Başarısız" }}
              </n-tag>
            </template>
          </n-list-item>
        </n-list>
        <n-text v-else :depth="3">Henüz bildirim gönderilmedi.</n-text>
      </section>
    </n-drawer-content>
  </n-drawer>
</template>
