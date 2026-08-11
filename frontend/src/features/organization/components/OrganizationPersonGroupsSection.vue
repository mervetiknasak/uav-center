<script setup>
import { Pencil, Plus, Trash2, Users } from "@lucide/vue";

import OrganizationPersonFields from "./OrganizationPersonFields.vue";

defineProps({
  personGroups: { type: Array, required: true },
  loading: { type: Boolean, required: true },
  canEdit: { type: Boolean, default: false }
});

const emit = defineEmits(["refresh", "open-editor", "request-delete"]);
</script>

<template>
  <div class="organization-tab-toolbar">
    <strong>Kişi Grupları</strong>
    <n-space>
      <n-button secondary :loading="loading" @click="emit('refresh')">Yenile</n-button>
      <n-button
        v-if="canEdit"
        circle
        type="primary"
        title="Yeni kişi grubu"
        aria-label="Yeni kişi grubu"
        @click="emit('open-editor', 'group')"
      >
        <template #icon><Plus :size="18" /></template>
      </n-button>
    </n-space>
  </div>

  <n-spin :show="loading">
    <n-empty v-if="!personGroups.length" description="Henüz kişi grubu oluşturulmadı">
      <template v-if="canEdit" #extra>
        <n-button type="primary" secondary @click="emit('open-editor', 'group')">
          <template #icon><Plus :size="16" /></template>
          İlk grubu oluştur
        </n-button>
      </template>
    </n-empty>

    <div v-else class="person-group-grid">
      <n-card v-for="group in personGroups" :key="group.id" class="person-group-card">
        <template #header>
          <div class="project-title">
            <Users :size="18" />
            <strong>{{ group.name }}</strong>
            <n-tag size="small">{{ group.people?.length ?? 0 }} kişi</n-tag>
          </div>
        </template>
        <template v-if="canEdit" #header-extra>
          <n-space>
            <n-button
              circle
              size="tiny"
              secondary
              title="Grubu düzenle"
              @click="emit('open-editor', 'group', group)"
            >
              <template #icon><Pencil :size="14" /></template>
            </n-button>
            <n-button
              circle
              size="tiny"
              type="error"
              secondary
              title="Grubu sil"
              @click="emit('request-delete', 'group', group)"
            >
              <template #icon><Trash2 :size="14" /></template>
            </n-button>
          </n-space>
        </template>

        <p v-if="group.description" class="panel-description">{{ group.description }}</p>
        <div class="responsible-toolbar">
          <span>Grup Üyeleri</span>
          <n-button
            v-if="canEdit"
            circle
            size="tiny"
            secondary
            title="Kişi ekle"
            @click="emit('open-editor', 'person', null, group)"
          >
            <template #icon><Plus :size="14" /></template>
          </n-button>
        </div>
        <n-empty
          v-if="!group.people?.length"
          size="small"
          description="Bu grupta henüz kimse yok"
        />
        <div v-else class="group-person-list">
          <div v-for="person in group.people" :key="person.id" class="group-person-row">
            <OrganizationPersonFields :person="person" />

            <n-button-group v-if="canEdit" size="tiny" class="responsible-actions">
              <n-button
                circle
                secondary
                title="Kişiyi düzenle"
                aria-label="Kişiyi düzenle"
                @click="emit('open-editor', 'person', person, group)"
              >
                <template #icon><Pencil :size="15" /></template>
              </n-button>
              <n-button
                circle
                type="error"
                secondary
                title="Kişiyi sil"
                aria-label="Kişiyi sil"
                @click="emit('request-delete', 'person', person)"
              >
                <template #icon><Trash2 :size="15" /></template>
              </n-button>
            </n-button-group>
          </div>
        </div>
      </n-card>
    </div>
  </n-spin>
</template>
