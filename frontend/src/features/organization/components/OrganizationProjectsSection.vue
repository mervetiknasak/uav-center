<script setup>
import { Plus } from "@lucide/vue";

import OrganizationProjectCard from "./OrganizationProjectCard.vue";

defineProps({
  projects: { type: Array, required: true },
  loading: { type: Boolean, required: true },
  canEdit: { type: Boolean, default: false }
});

const emit = defineEmits([
  "refresh",
  "open-editor",
  "request-delete",
  "reorder-responsibles",
  "remove-responsible"
]);
</script>

<template>
  <div class="organization-tab-toolbar">
    <strong>Projeler ve Paneller</strong>
    <n-space>
      <n-button secondary :loading="loading" @click="emit('refresh')">Yenile</n-button>
      <n-button
        v-if="canEdit"
        circle
        type="primary"
        title="Yeni proje"
        aria-label="Yeni proje"
        @click="emit('open-editor', 'project')"
      >
        <template #icon><Plus :size="18" /></template>
      </n-button>
    </n-space>
  </div>

  <n-spin :show="loading">
    <n-empty v-if="!projects.length" description="Henüz proje eklenmedi">
      <template v-if="canEdit" #extra>
        <n-button
          circle
          type="primary"
          title="İlk projeyi ekle"
          aria-label="İlk projeyi ekle"
          @click="emit('open-editor', 'project')"
        >
          <template #icon><Plus :size="18" /></template>
        </n-button>
      </template>
    </n-empty>

    <div v-else class="project-grid">
      <OrganizationProjectCard
        v-for="project in projects"
        :key="project.id"
        :project="project"
        :can-edit="canEdit"
        @open-editor="(type, item, parent) => emit('open-editor', type, item, parent)"
        @request-delete="(type, item) => emit('request-delete', type, item)"
        @reorder-responsibles="(panel, items) => emit('reorder-responsibles', panel, items)"
        @remove-responsible="(panel, index) => emit('remove-responsible', panel, index)"
      />
    </div>
  </n-spin>
</template>
