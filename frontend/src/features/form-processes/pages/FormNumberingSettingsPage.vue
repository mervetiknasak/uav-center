<script setup>
import { onMounted } from "vue";
import { useRouter } from "vue-router";
import { useAppContext } from "../../../app/bootstrap";
import { useNumberingSettings } from "../composables/useNumberingSettings";

const router = useRouter();
const { api } = useAppContext();
const settings = useNumberingSettings({ apiFetch: api.apiFetch });
const sourceKinds = [
  { label: "Form alanı", value: "field" },
  { label: "Sabit değer", value: "fixed" },
  { label: "Kullanıcı girişi", value: "manual" }
];
onMounted(settings.load);
</script>

<template>
  <section class="form-process-editor-page">
    <n-page-header
      title="Numaratör Ayarları"
      subtitle="Numara formatlarını form alanlarına bağlayın ve context kaynaklarını belirleyin."
      @back="router.push({ name: 'form-processes' })"
    />
    <n-alert v-if="settings.error.value" type="error" class="form-process-alert">{{
      settings.error.value
    }}</n-alert>
    <n-alert v-if="settings.notice.value" type="success" class="form-process-alert">{{
      settings.notice.value
    }}</n-alert>
    <n-spin :show="settings.loading.value">
      <n-space vertical :size="20">
        <n-card :title="settings.form.id ? 'Eşleştirmeyi düzenle' : 'Yeni eşleştirme'" size="small">
          <n-form label-placement="top">
            <n-grid cols="1 m:2" responsive="screen" :x-gap="16">
              <n-form-item-gi label="Form şablonu" required
                ><n-select
                  :value="settings.form.template_code"
                  :options="settings.templateOptions.value"
                  :disabled="Boolean(settings.form.id)"
                  filterable
                  placeholder="Form seçin"
                  @update:value="settings.setTemplate"
              /></n-form-item-gi>
              <n-form-item-gi label="Hedef alan" required
                ><n-select
                  v-model:value="settings.form.target_field"
                  :options="settings.targetOptions.value"
                  :disabled="Boolean(settings.form.id) || !settings.form.template_code"
                  filterable
                  placeholder="Numaranın yazılacağı alan"
              /></n-form-item-gi>
              <n-form-item-gi label="Numaratör formatı" required
                ><n-select
                  :value="settings.form.format_code"
                  :options="settings.formatOptions.value"
                  filterable
                  placeholder="Format seçin"
                  @update:value="settings.setFormat"
              /></n-form-item-gi>
              <n-form-item-gi label="Eşleştirme durumu"
                ><n-switch v-model:value="settings.form.enabled"
                  ><template #checked>Etkin</template
                  ><template #unchecked>Devre dışı</template></n-switch
                ></n-form-item-gi
              >
            </n-grid>
            <n-text v-if="settings.format.value?.preview" depth="3"
              >Format örneği: {{ settings.format.value.preview }}</n-text
            >
            <n-divider v-if="settings.format.value?.required_context.length"
              >Context kaynakları</n-divider
            >
            <div
              v-for="item in settings.format.value?.required_context || []"
              :key="item.key"
              class="form-numbering-context-row"
            >
              <n-form-item :label="`${item.key} · en fazla ${item.max_length} karakter`" required>
                <n-select
                  :value="settings.form.context_sources[item.key]?.source"
                  :options="
                    item.required
                      ? sourceKinds
                      : [...sourceKinds, { label: 'Format varsayılanı', value: 'default' }]
                  "
                  @update:value="settings.form.context_sources[item.key] = { source: $event }"
                />
              </n-form-item>
              <n-form-item
                v-if="settings.form.context_sources[item.key]?.source === 'field'"
                label="Kaynak alan"
              >
                <n-select
                  v-model:value="settings.form.context_sources[item.key].field"
                  :options="
                    settings.sourceOptions.value.filter(
                      (field) => field.value !== settings.form.target_field
                    )
                  "
                  filterable
                  placeholder="Form alanını seçin"
                />
              </n-form-item>
              <n-form-item
                v-else-if="settings.form.context_sources[item.key]?.source === 'fixed'"
                label="Sabit değer"
              >
                <n-input
                  v-model:value="settings.form.context_sources[item.key].value"
                  :maxlength="item.max_length"
                  show-count
                />
              </n-form-item>
              <n-text v-else depth="3">{{
                settings.form.context_sources[item.key]?.source === "default"
                  ? `Varsayılan: ${item.default ?? ""}`
                  : "Numara alınırken kullanıcıdan istenir."
              }}</n-text>
            </div>
            <n-space justify="end">
              <n-button :disabled="settings.saving.value" @click="settings.reset">Temizle</n-button>
              <n-button
                type="primary"
                :loading="settings.saving.value"
                :disabled="settings.loading.value"
                @click="settings.save"
                >Eşleştirmeyi kaydet</n-button
              >
            </n-space>
          </n-form>
        </n-card>
        <n-card title="Kayıtlı eşleştirmeler" size="small">
          <n-empty
            v-if="!settings.mappings.value.length"
            description="Henüz numara eşleştirmesi yok."
          />
          <n-list v-else>
            <n-list-item v-for="mapping in settings.mappings.value" :key="mapping.id">
              <n-thing
                :title="`${settings.templates.value.find((item) => item.code === mapping.template_code)?.form_number || mapping.template_code} → ${mapping.target_field === 'record_number' ? 'Kayıt numarası' : mapping.target_field}`"
                :description="mapping.format_code"
              />
              <template #suffix
                ><n-space align="center"
                  ><n-tag :type="mapping.enabled ? 'success' : 'default'">{{
                    mapping.enabled ? "Etkin" : "Devre dışı"
                  }}</n-tag
                  ><n-button :disabled="settings.saving.value" @click="settings.edit(mapping)"
                    >Düzenle</n-button
                  ></n-space
                ></template
              >
            </n-list-item>
          </n-list>
          <n-button text :loading="settings.loading.value" @click="settings.load"
            >Formatları ve eşleştirmeleri yenile</n-button
          >
        </n-card>
      </n-space>
    </n-spin>
  </section>
</template>
