<script setup>
import { Pencil, Plus, Trash2 } from "@lucide/vue";

import OrganizationPanelItem from "./OrganizationPanelItem.vue";

defineProps({
  project: { type: Object, required: true },
  canEdit: { type: Boolean, default: false }
});

const emit = defineEmits([
  "open-editor",
  "request-delete",
  "reorder-responsibles",
  "remove-responsible"
]);
</script>

<template>
  <n-card class="project-card">
    <template #header>
      <div class="project-title">
        <n-tag :type="project.is_active ? 'success' : 'default'" size="small">
          {{ project.code }}
        </n-tag>
        <strong>{{ project.name }}</strong>
      </div>
    </template>
    <template v-if="canEdit" #header-extra>
      <n-space>
        <n-button
          circle
          size="tiny"
          secondary
          title="Projeyi düzenle"
          aria-label="Projeyi düzenle"
          @click="emit('open-editor', 'project', project)"
        >
          <template #icon><Pencil :size="14" /></template>
        </n-button>
        <n-button
          circle
          size="tiny"
          type="error"
          secondary
          title="Projeyi sil"
          aria-label="Projeyi sil"
          @click="emit('request-delete', 'project', project)"
        >
          <template #icon><Trash2 :size="14" /></template>
        </n-button>
      </n-space>
    </template>

    <p v-if="project.description" class="project-description">{{ project.description }}</p>
    <n-alert v-if="!project.is_active" type="warning" :show-icon="false">
      Bu proje pasif durumda.
    </n-alert>

    <div class="panel-toolbar">
      <strong>Alt Paneller</strong>
      <n-button
        v-if="canEdit"
        circle
        size="tiny"
        type="primary"
        secondary
        title="Panel ekle"
        aria-label="Panel ekle"
        @click="emit('open-editor', 'panel', null, project)"
      >
        <template #icon><Plus :size="14" /></template>
      </n-button>
    </div>

    <n-empty v-if="!project.panels.length" size="small" description="Alt panel bulunmuyor" />
    <n-collapse v-else accordion>
      <OrganizationPanelItem
        v-for="panel in project.panels"
        :key="panel.id"
        :panel="panel"
        :can-edit="canEdit"
        @open-editor="(type, item, parent) => emit('open-editor', type, item, parent || project)"
        @request-delete="(type, item) => emit('request-delete', type, item)"
        @reorder-responsibles="(item, values) => emit('reorder-responsibles', item, values)"
        @remove-responsible="(item, index) => emit('remove-responsible', item, index)"
      />
    </n-collapse>
  </n-card>
</template>
