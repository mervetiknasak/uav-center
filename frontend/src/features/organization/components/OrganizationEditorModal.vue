<script setup>
import { Save } from "@lucide/vue";

defineProps({
  show: { type: Boolean, required: true },
  title: { type: String, required: true },
  editorType: { type: String, required: true },
  form: { type: Object, required: true },
  saving: { type: Boolean, required: true },
  canSubmit: { type: Boolean, required: true }
});

const emit = defineEmits(["update:show", "update-field", "submit"]);
</script>

<template>
  <n-modal
    :show="show"
    preset="card"
    :title="title"
    class="organization-modal"
    @update:show="emit('update:show', $event)"
  >
    <n-form @submit.prevent="emit('submit')">
      <n-form-item label="Ad" required>
        <n-input
          :value="form.name"
          placeholder="Ad girin"
          @update:value="emit('update-field', 'name', $event)"
        />
      </n-form-item>
      <template v-if="editorType === 'project'">
        <n-form-item label="Proje Kodu" required>
          <n-input
            :value="form.code"
            placeholder="Örn. UAV-01"
            @update:value="emit('update-field', 'code', $event)"
          />
        </n-form-item>
        <n-form-item label="Açıklama">
          <n-input
            :value="form.description"
            type="textarea"
            @update:value="emit('update-field', 'description', $event)"
          />
        </n-form-item>
        <n-form-item label="Durum">
          <n-switch
            :value="form.is_active"
            @update:value="emit('update-field', 'is_active', $event)"
          />
          &nbsp; Aktif
        </n-form-item>
      </template>
      <template v-else-if="editorType === 'panel' || editorType === 'group'">
        <n-form-item label="Açıklama">
          <n-input
            :value="form.description"
            type="textarea"
            @update:value="emit('update-field', 'description', $event)"
          />
        </n-form-item>
      </template>
      <template v-else>
        <n-form-item label="Görev / Ünvan">
          <n-input :value="form.title" @update:value="emit('update-field', 'title', $event)" />
        </n-form-item>
        <n-form-item label="E-posta">
          <n-input
            :value="form.email"
            type="email"
            @update:value="emit('update-field', 'email', $event)"
          />
        </n-form-item>
        <n-form-item label="Username">
          <n-input
            :value="form.username"
            placeholder="Kullanıcı adı"
            @update:value="emit('update-field', 'username', $event)"
          />
        </n-form-item>
      </template>
      <n-form-item v-if="!['responsible', 'person'].includes(editorType)" label="Sıra">
        <n-input-number
          :value="form.order"
          :min="0"
          @update:value="emit('update-field', 'order', $event)"
        />
      </n-form-item>
      <n-space justify="end">
        <n-button @click="emit('update:show', false)">Vazgeç</n-button>
        <n-button
          circle
          attr-type="submit"
          type="primary"
          title="Kaydet"
          aria-label="Kaydet"
          :loading="saving"
          :disabled="!canSubmit"
        >
          <template #icon><Save :size="17" /></template>
        </n-button>
      </n-space>
    </n-form>
  </n-modal>
</template>
