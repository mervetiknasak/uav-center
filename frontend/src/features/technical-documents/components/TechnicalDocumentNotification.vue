<script setup>
import { Send } from "@lucide/vue";

defineProps({
  show: { type: Boolean, required: true },
  document: { type: Object, default: null },
  form: { type: Object, required: true },
  notifyingId: { type: Number, default: null }
});

const emit = defineEmits(["update:show", "submit"]);
</script>

<template>
  <n-modal
    :show="show"
    preset="card"
    title="Panel sorumlularını bilgilendir"
    class="td-notify-modal"
    @update:show="emit('update:show', $event)"
  >
    <template v-if="document">
      <n-alert
        class="td-recipient-box"
        type="info"
        :title="`${(document.notification_recipients || []).length} panel sorumlusu`"
      >
        <n-text>
          {{
            (document.notification_recipients || [])
              .map((recipient) => `${recipient.name} · ${recipient.panel}`)
              .join(", ")
          }}
        </n-text>
      </n-alert>
      <n-form label-placement="top" @submit.prevent="emit('submit')">
        <n-form-item label="Konu">
          <n-input v-model:value="form.subject" />
        </n-form-item>
        <n-form-item label="Mesaj">
          <n-input v-model:value="form.message" type="textarea" :rows="8" />
        </n-form-item>
        <n-divider />
        <n-flex justify="end">
          <n-button @click="emit('update:show', false)">Vazgeç</n-button>
          <n-button attr-type="submit" type="primary" :loading="notifyingId === document.id">
            <template #icon
              ><n-icon><Send /></n-icon
            ></template>
            E-postayı gönder
          </n-button>
        </n-flex>
      </n-form>
    </template>
  </n-modal>
</template>
