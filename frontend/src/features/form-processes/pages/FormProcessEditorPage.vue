<script setup>
import { onBeforeUnmount, onMounted } from "vue";
import { ArrowLeft, Check, Download, Eye, Save } from "@lucide/vue";
import { onBeforeRouteLeave, useRoute, useRouter } from "vue-router";

import { useAppContext } from "../../../app/bootstrap";
import FormProcessFieldsStep from "../components/FormProcessFieldsStep.vue";
import FormProcessReviewStep from "../components/FormProcessReviewStep.vue";
import FormProcessTemplateStep from "../components/FormProcessTemplateStep.vue";
import { useFormProcessEditor } from "../composables/useFormProcessEditor";

const route = useRoute();
const router = useRouter();
const { api } = useAppContext();
const editor = useFormProcessEditor({
  apiFetch: api.apiFetch,
  router,
  recordId: route.params.recordId || null
});

function leaveWarning(event) {
  if (!editor.dirty.value) return;
  event.preventDefault();
  event.returnValue = "";
}

onBeforeRouteLeave(() => {
  if (!editor.dirty.value) return true;
  return window.confirm("Kaydedilmemiş değişiklikleriniz var. Sayfadan ayrılmak istiyor musunuz?");
});

onMounted(() => {
  window.addEventListener("beforeunload", leaveWarning);
  editor.load();
});
onBeforeUnmount(() => window.removeEventListener("beforeunload", leaveWarning));
</script>

<template>
  <section class="form-process-editor-page">
    <n-page-header
      :title="editor.record.value ? 'FM kaydını düzenle' : 'Yeni FM form kaydı'"
      subtitle="Süreci ve şablonu seçin, formu doldurun ve tamamlamadan önce inceleyin."
      @back="router.push({ name: 'form-processes' })"
    >
      <template #back
        ><n-icon><ArrowLeft /></n-icon
      ></template>
      <template #extra>
        <n-tag v-if="editor.record.value" :bordered="false">
          {{ editor.record.value.status_display }}
        </n-tag>
      </template>
    </n-page-header>

    <n-spin :show="editor.loading.value">
      <n-alert v-if="editor.error.value" type="error" class="form-process-alert">
        {{ editor.error.value }}
      </n-alert>
      <n-alert v-if="editor.notice.value" type="success" class="form-process-alert">
        {{ editor.notice.value }}
      </n-alert>
      <n-alert
        v-if="editor.archived.value"
        type="warning"
        title="Arşivlenmiş kayıt"
        class="form-process-alert"
      >
        Bu kayıt yeniden açılmadan düzenlenemez. Kayıt listesindeki “Yeniden aç” işlemini kullanın.
      </n-alert>

      <template v-if="editor.ready.value && !editor.archived.value">
        <nav class="form-process-steps" aria-label="Form oluşturma adımları">
          <button
            type="button"
            :class="{ 'is-active': editor.currentStep.value === 1 }"
            :disabled="editor.templateLocked.value"
            @click="editor.currentStep.value = 1"
          >
            <span>1</span>Süreç ve şablon
          </button>
          <button
            type="button"
            :class="{ 'is-active': editor.currentStep.value === 2 }"
            :disabled="!editor.selectedTemplate.value"
            @click="editor.currentStep.value = 2"
          >
            <span>2</span>Form alanları
          </button>
          <button
            type="button"
            :class="{ 'is-active': editor.currentStep.value === 3 }"
            :disabled="!editor.selectedTemplate.value"
            @click="editor.review"
          >
            <span>3</span>İncele ve tamamla
          </button>
        </nav>

        <n-card
          v-if="editor.templateLocked.value"
          size="small"
          class="form-process-locked-template"
        >
          <n-text depth="3">Kayıt şablonu</n-text>
          <strong>
            {{ editor.selectedTemplate.value?.process_name }} ·
            {{ editor.selectedTemplate.value?.form_number }} —
            {{ editor.selectedTemplate.value?.title }}
          </strong>
          <n-text depth="3">Kayıt sonrası süreç ve şablon değiştirilemez.</n-text>
        </n-card>

        <FormProcessTemplateStep
          v-if="editor.currentStep.value === 1"
          :processes="editor.processes.value"
          :templates="editor.templates.value"
          :process-code="editor.form.process_code"
          :template-code="editor.form.template_code"
          :error="editor.validationErrors.value.template_code"
          @select-process="editor.selectProcess"
          @select-template="editor.selectTemplate"
        />

        <FormProcessFieldsStep
          v-else-if="editor.currentStep.value === 2 && editor.selectedTemplate.value"
          :form="editor.form"
          :template="editor.selectedTemplate.value"
          :errors="editor.validationErrors.value"
          @update-identity="editor.updateIdentity"
          @update-field="editor.updateField"
          @update-notes="editor.updateNotes"
        />

        <FormProcessReviewStep
          v-else-if="editor.currentStep.value === 3 && editor.selectedTemplate.value"
          :form="editor.form"
          :template="editor.selectedTemplate.value"
          :record="editor.record.value"
        />

        <div class="form-process-action-bar">
          <n-space justify="space-between" align="center">
            <n-button
              v-if="editor.currentStep.value === 1"
              @click="router.push({ name: 'form-processes' })"
            >
              Vazgeç
            </n-button>
            <n-button
              v-else-if="editor.currentStep.value === 2 && !editor.record.value"
              @click="editor.currentStep.value = 1"
            >
              Şablona dön
            </n-button>
            <n-button
              v-else-if="editor.currentStep.value === 2"
              @click="router.push({ name: 'form-processes' })"
            >
              Kayıtlara dön
            </n-button>
            <n-button v-else @click="editor.currentStep.value = 2">Forma dön</n-button>

            <n-space>
              <n-button
                v-if="editor.currentStep.value === 1"
                type="primary"
                :disabled="!editor.selectedTemplate.value"
                @click="editor.goToFields"
              >
                Form alanlarına devam et
              </n-button>
              <template v-else-if="editor.currentStep.value === 2">
                <n-button secondary :loading="editor.saving.value" @click="editor.saveDraft">
                  <template #icon
                    ><n-icon><Save /></n-icon
                  ></template>
                  Taslak kaydet
                </n-button>
                <n-button type="primary" :disabled="editor.saving.value" @click="editor.review">
                  <template #icon
                    ><n-icon><Eye /></n-icon
                  ></template>
                  İncele
                </n-button>
              </template>
              <n-button
                v-else-if="editor.record.value?.status === 'approved'"
                type="primary"
                @click="editor.download"
              >
                <template #icon
                  ><n-icon><Download /></n-icon
                ></template>
                Word indir
              </n-button>
              <template v-else>
                <n-button secondary :loading="editor.saving.value" @click="editor.saveDraft">
                  <template #icon
                    ><n-icon><Save /></n-icon
                  ></template>
                  Taslak kaydet
                </n-button>
                <n-button type="primary" :loading="editor.saving.value" @click="editor.complete">
                  <template #icon
                    ><n-icon><Check /></n-icon
                  ></template>
                  Tamamla
                </n-button>
              </template>
            </n-space>
          </n-space>
        </div>
      </template>
    </n-spin>
  </section>
</template>
