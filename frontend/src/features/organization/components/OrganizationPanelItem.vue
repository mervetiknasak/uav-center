<script setup>
import { ArrowDown, ArrowUp, Pencil, Plus, Trash2 } from "@lucide/vue";

import OrganizationPersonFields from "./OrganizationPersonFields.vue";

defineProps({
  panel: { type: Object, required: true },
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
  <n-collapse-item :name="panel.id">
    <template #header>
      <div class="panel-title">
        <strong>{{ panel.name }}</strong>
        <n-tag size="small">{{ panel.responsibles.length }} sorumlu</n-tag>
      </div>
    </template>
    <template v-if="canEdit" #header-extra>
      <n-space @click.stop>
        <n-button
          circle
          size="tiny"
          quaternary
          title="Paneli düzenle"
          aria-label="Paneli düzenle"
          @click="emit('open-editor', 'panel', panel)"
        >
          <template #icon><Pencil :size="14" /></template>
        </n-button>
        <n-button
          circle
          size="tiny"
          type="error"
          quaternary
          title="Paneli sil"
          aria-label="Paneli sil"
          @click="emit('request-delete', 'panel', panel)"
        >
          <template #icon><Trash2 :size="14" /></template>
        </n-button>
      </n-space>
    </template>

    <p v-if="panel.description" class="panel-description">{{ panel.description }}</p>
    <div class="responsible-toolbar">
      <span>Sorumlular</span>
      <n-button
        v-if="canEdit"
        circle
        size="tiny"
        secondary
        title="Sorumlu ekle"
        aria-label="Sorumlu ekle"
        @click="emit('open-editor', 'responsible', null, panel)"
      >
        <template #icon><Plus :size="14" /></template>
      </n-button>
    </div>
    <n-empty v-if="!panel.responsibles.length" size="small" description="Sorumlu atanmamış" />
    <n-dynamic-input
      v-else
      :value="panel.responsibles"
      key-field="id"
      item-class="responsible-dynamic-item"
      :show-sort-button="canEdit"
      :disabled="!canEdit"
      @remove="(index) => emit('remove-responsible', panel, index)"
      @update:value="(items) => emit('reorder-responsibles', panel, items)"
    >
      <template #default="{ value: person }">
        <OrganizationPersonFields :person="person" />
      </template>
      <template v-if="canEdit" #action="{ value: person, index, remove, move }">
        <n-button-group size="tiny" class="responsible-actions">
          <n-button
            circle
            secondary
            title="Sorumluyu düzenle"
            aria-label="Sorumluyu düzenle"
            @click="emit('open-editor', 'responsible', person, panel)"
          >
            <template #icon><Pencil :size="15" /></template>
          </n-button>
          <n-button
            circle
            type="error"
            secondary
            title="Sorumluyu sil"
            aria-label="Sorumluyu sil"
            @click="remove(index)"
          >
            <template #icon><Trash2 :size="15" /></template>
          </n-button>
          <n-button
            circle
            secondary
            title="Yukarı taşı"
            aria-label="Yukarı taşı"
            :disabled="index === 0"
            @click="move('up', index)"
          >
            <template #icon><ArrowUp :size="15" /></template>
          </n-button>
          <n-button
            circle
            secondary
            title="Aşağı taşı"
            aria-label="Aşağı taşı"
            :disabled="index === panel.responsibles.length - 1"
            @click="move('down', index)"
          >
            <template #icon><ArrowDown :size="15" /></template>
          </n-button>
        </n-button-group>
      </template>
    </n-dynamic-input>
  </n-collapse-item>
</template>
