<script setup>
defineProps({
  users: {
    type: Array,
    required: true
  },
  loading: {
    type: Boolean,
    required: true
  },
  error: {
    type: String,
    default: ""
  },
  updatingUserId: {
    type: Number,
    default: null
  }
});

const emit = defineEmits(["refresh", "update-status"]);
</script>

<template>
  <section class="admin-membership-view">
    <div class="page-heading">
      <p>Admin</p>
      <h1>Üye Yönetimi</h1>
    </div>

    <n-card title="Üyelik Akışı" size="small">
      <n-space vertical :size="16">
        <div class="admin-membership-toolbar">
          <n-button secondary :loading="loading" @click="emit('refresh')">
            Listeyi Yenile
          </n-button>
        </div>

        <n-alert v-if="error" type="error" title="Üye yönetimi hatası">
          {{ error }}
        </n-alert>

        <n-spin :show="loading">
          <n-empty v-if="users.length === 0" description="Henüz kullanıcı yok" />
          <n-list v-else hoverable>
            <n-list-item v-for="user in users" :key="user.id">
              <div class="user-row">
                <n-thing :title="user.username" :description="user.email || 'E-posta yok'" />
                <div class="user-actions">
                  <n-tag :type="user.is_active ? 'success' : 'warning'">
                    {{ user.is_active ? "Aktif" : "Pending" }}
                  </n-tag>
                  <n-tag v-if="user.is_staff" type="info">Admin</n-tag>
                  <n-button
                    v-if="!user.is_active"
                    size="small"
                    type="primary"
                    secondary
                    :loading="updatingUserId === user.id"
                    @click="emit('update-status', user, true)"
                  >
                    Onayla
                  </n-button>
                  <n-button
                    v-else
                    size="small"
                    type="error"
                    secondary
                    :loading="updatingUserId === user.id"
                    @click="emit('update-status', user, false)"
                  >
                    Devre Dışı Bırak
                  </n-button>
                </div>
              </div>
            </n-list-item>
          </n-list>
        </n-spin>
      </n-space>
    </n-card>
  </section>
</template>
