<script setup>
const props = defineProps({
  health: {
    type: Object,
    default: null
  },
  apiStatus: {
    type: String,
    required: true
  },
  error: {
    type: String,
    default: ""
  },
  loading: {
    type: Boolean,
    required: true
  },
  documents: {
    type: Array,
    required: true
  },
  documentsLoading: {
    type: Boolean,
    required: true
  },
  adminUsers: {
    type: Array,
    required: true
  },
  adminUsersLoading: {
    type: Boolean,
    required: true
  },
  adminUsersError: {
    type: String,
    default: ""
  },
  currentUser: {
    type: Object,
    required: true
  },
  apiBaseUrl: {
    type: String,
    required: true
  }
});

const emit = defineEmits(["check-backend", "refresh-documents", "refresh-users"]);

function countDocuments(status) {
  return props.documents.filter((document) => document.status === status).length;
}

function countUsers(predicate) {
  return props.adminUsers.filter(predicate).length;
}
</script>

<template>
  <section class="system-view">
    <div class="page-heading">
      <p>Sistem</p>
      <h1>Geliştirme Kontrol Paneli</h1>
    </div>

    <div class="system-grid">
      <n-card title="Backend Durumu" size="small">
        <n-space vertical :size="16">
          <n-alert :type="error ? 'error' : health ? 'success' : 'info'" :title="apiStatus">
            <span v-if="error">Hata: {{ error }}</span>
            <span v-else-if="health">
              {{ health.service }} servisi {{ health.timestamp }} zamanında yanıt verdi.
            </span>
            <span v-else>Backend bağlantısı için kontrol başlatılabilir.</span>
          </n-alert>

          <n-button type="primary" :loading="loading" @click="emit('check-backend')">
            Backend'i Test Et
          </n-button>
        </n-space>
      </n-card>

      <n-card title="Oturum ve Ortam" size="small">
        <n-descriptions :column="1" bordered size="small">
          <n-descriptions-item label="Kullanıcı">{{ currentUser.username }}</n-descriptions-item>
          <n-descriptions-item label="Rol">Admin</n-descriptions-item>
          <n-descriptions-item label="API">{{
            apiBaseUrl || "Aynı origin / proxy"
          }}</n-descriptions-item>
        </n-descriptions>
      </n-card>

      <n-card title="Belge İşleme" size="small">
        <n-space vertical :size="16">
          <n-descriptions :column="2" bordered size="small">
            <n-descriptions-item label="Toplam">{{ documents.length }}</n-descriptions-item>
            <n-descriptions-item label="İşlendi">{{
              countDocuments("processed")
            }}</n-descriptions-item>
            <n-descriptions-item label="Pending">{{
              countDocuments("pending")
            }}</n-descriptions-item>
            <n-descriptions-item label="Hatalı">{{ countDocuments("failed") }}</n-descriptions-item>
          </n-descriptions>

          <n-button secondary :loading="documentsLoading" @click="emit('refresh-documents')">
            Belgeleri Yenile
          </n-button>
        </n-space>
      </n-card>

      <n-card title="Üyelik Akışı" size="small">
        <n-space vertical :size="16">
          <n-alert v-if="adminUsersError" type="error" title="Üyelik verisi alınamadı">
            {{ adminUsersError }}
          </n-alert>

          <n-descriptions :column="2" bordered size="small">
            <n-descriptions-item label="Toplam">{{ adminUsers.length }}</n-descriptions-item>
            <n-descriptions-item label="Pending">
              {{ countUsers((user) => !user.is_active) }}
            </n-descriptions-item>
            <n-descriptions-item label="Aktif">
              {{ countUsers((user) => user.is_active) }}
            </n-descriptions-item>
            <n-descriptions-item label="Admin">
              {{ countUsers((user) => user.is_staff) }}
            </n-descriptions-item>
          </n-descriptions>

          <n-button secondary :loading="adminUsersLoading" @click="emit('refresh-users')">
            Üyeleri Yenile
          </n-button>
        </n-space>
      </n-card>

      <n-card title="Desteklenen Dosyalar" size="small">
        <n-descriptions :column="1" bordered size="small">
          <n-descriptions-item label="PDF">.pdf</n-descriptions-item>
          <n-descriptions-item label="Office">.docx, .xlsx, .pptx</n-descriptions-item>
          <n-descriptions-item label="Metin">.txt, .csv, .md</n-descriptions-item>
        </n-descriptions>
      </n-card>

      <n-card title="Hızlı Kontroller" size="small">
        <n-space>
          <n-button secondary :loading="loading" @click="emit('check-backend')"> Sağlık </n-button>
          <n-button secondary :loading="documentsLoading" @click="emit('refresh-documents')">
            Belgeler
          </n-button>
          <n-button secondary :loading="adminUsersLoading" @click="emit('refresh-users')">
            Üyeler
          </n-button>
        </n-space>
      </n-card>
    </div>
  </section>
</template>
