<script setup>
import { computed, reactive, ref } from "vue";
import { ArrowDown, ArrowUp, Pencil, Plus, Save, Trash2 } from "@lucide/vue";

const props = defineProps({
  projects: { type: Array, required: true },
  loading: { type: Boolean, required: true },
  saving: { type: Boolean, required: true },
  error: { type: String, default: "" },
  canEdit: { type: Boolean, default: false }
});

const emit = defineEmits(["refresh", "save", "delete", "reorder-responsibles"]);
const showModal = ref(false);
const editorType = ref("project");
const editorId = ref(null);
const parentId = ref(null);
const form = reactive({});

const modalTitle = computed(() => {
  const labels = { project: "Proje", panel: "Alt Panel", responsible: "Sorumlu" };
  return `${editorId.value ? "Düzenle" : "Yeni"} ${labels[editorType.value]}`;
});

function openEditor(type, item = null, parent = null) {
  editorType.value = type;
  editorId.value = item?.id ?? null;
  parentId.value = parent?.id ?? null;
  Object.keys(form).forEach((key) => delete form[key]);
  if (type === "project") {
    Object.assign(form, {
      name: item?.name ?? "",
      code: item?.code ?? "",
      description: item?.description ?? "",
      is_active: item?.is_active ?? true,
      order: item?.order ?? 0
    });
  } else if (type === "panel") {
    Object.assign(form, {
      name: item?.name ?? "",
      description: item?.description ?? "",
      order: item?.order ?? 0
    });
  } else {
    Object.assign(form, {
      name: item?.name ?? "",
      title: item?.title ?? "",
      email: item?.email ?? "",
      phone: item?.phone ?? "",
      username: item?.username ?? ""
    });
  }
  showModal.value = true;
}

function submit() {
  emit("save", {
    type: editorType.value,
    id: editorId.value,
    parentId: parentId.value,
    payload: { ...form },
    done: () => (showModal.value = false)
  });
}

function requestDelete(type, item) {
  if (window.confirm(`“${item.name}” kaydı silinsin mi? Alt kayıtlar da silinebilir.`)) {
    emit("delete", { type, item });
  }
}

function reorderResponsibles(panel, reorderedItems) {
  if (reorderedItems.length !== panel.responsibles.length) return;
  emit("reorder-responsibles", {
    panelId: panel.id,
    items: reorderedItems.map((item, index) => ({ ...item, order: index }))
  });
}

function removeResponsible(panel, index) {
  emit("delete", { type: "responsible", item: panel.responsibles[index] });
}
</script>

<template>
  <section class="organization-view">
    <div class="page-heading organization-heading">
      <div>
        <p>{{ canEdit ? "Yönetim" : "Organizasyon" }}</p>
        <h1>Projeler ve Paneller</h1>
        <span>Projeleri, alt panelleri ve sorumluları tek yerden görüntüleyin.</span>
      </div>
      <n-space>
        <n-button secondary :loading="loading" @click="emit('refresh')">Yenile</n-button>
        <n-button
          v-if="canEdit"
          circle
          type="primary"
          title="Yeni proje"
          aria-label="Yeni proje"
          @click="openEditor('project')"
        >
          <template #icon><Plus :size="18" /></template>
        </n-button>
      </n-space>
    </div>

    <n-alert v-if="error" type="error" title="Organizasyon bilgileri alınamadı">{{ error }}</n-alert>

    <n-spin :show="loading">
      <n-empty v-if="!projects.length" description="Henüz proje eklenmedi">
        <template v-if="canEdit" #extra>
          <n-button
            circle
            type="primary"
            title="İlk projeyi ekle"
            aria-label="İlk projeyi ekle"
            @click="openEditor('project')"
          >
            <template #icon><Plus :size="18" /></template>
          </n-button>
        </template>
      </n-empty>

      <div v-else class="project-grid">
        <n-card v-for="project in projects" :key="project.id" class="project-card">
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
                @click="openEditor('project', project)"
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
                @click="requestDelete('project', project)"
              >
                <template #icon><Trash2 :size="14" /></template>
              </n-button>
            </n-space>
          </template>

          <p v-if="project.description" class="project-description">{{ project.description }}</p>
          <n-alert v-if="!project.is_active" type="warning" :show-icon="false">Bu proje pasif durumda.</n-alert>

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
              @click="openEditor('panel', null, project)"
            >
              <template #icon><Plus :size="14" /></template>
            </n-button>
          </div>

          <n-empty v-if="!project.panels.length" size="small" description="Alt panel bulunmuyor" />
          <n-collapse v-else accordion>
            <n-collapse-item v-for="panel in project.panels" :key="panel.id" :name="panel.id">
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
                    @click="openEditor('panel', panel, project)"
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
                    @click="requestDelete('panel', panel)"
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
                  @click="openEditor('responsible', null, panel)"
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
                @remove="(index) => removeResponsible(panel, index)"
                @update:value="(items) => reorderResponsibles(panel, items)"
              >
                <template #default="{ value: person }">
                  <div class="responsible-inline">
                    <strong>{{ person.name }}</strong>
                    <span>{{ person.title || "Görev bilgisi yok" }}</span>
                    <a v-if="person.email" :href="`mailto:${person.email}`">{{ person.email }}</a>
                    <span v-else>—</span>
                    <span>{{ person.phone || "—" }}</span>
                    <n-tag v-if="person.username" size="small">{{ person.username }}</n-tag>
                  </div>
                </template>
                <template v-if="canEdit" #action="{ value: person, index, remove, move }">
                  <n-button-group size="tiny" class="responsible-actions">
                    <n-button
                      circle
                      secondary
                      title="Sorumluyu düzenle"
                      aria-label="Sorumluyu düzenle"
                      @click="openEditor('responsible', person, panel)"
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
          </n-collapse>
        </n-card>
      </div>
    </n-spin>

    <n-modal v-model:show="showModal" preset="card" :title="modalTitle" class="organization-modal">
      <n-form @submit.prevent="submit">
        <n-form-item label="Ad" required>
          <n-input v-model:value="form.name" placeholder="Ad girin" />
        </n-form-item>
        <template v-if="editorType === 'project'">
          <n-form-item label="Proje Kodu" required>
            <n-input v-model:value="form.code" placeholder="Örn. UAV-01" />
          </n-form-item>
          <n-form-item label="Açıklama">
            <n-input v-model:value="form.description" type="textarea" />
          </n-form-item>
          <n-form-item label="Durum"><n-switch v-model:value="form.is_active" />&nbsp; Aktif</n-form-item>
        </template>
        <template v-else-if="editorType === 'panel'">
          <n-form-item label="Açıklama"><n-input v-model:value="form.description" type="textarea" /></n-form-item>
        </template>
        <template v-else>
          <n-form-item label="Görev / Ünvan"><n-input v-model:value="form.title" /></n-form-item>
          <n-form-item label="E-posta"><n-input v-model:value="form.email" type="email" /></n-form-item>
          <n-form-item label="Telefon"><n-input v-model:value="form.phone" /></n-form-item>
          <n-form-item label="Username">
            <n-input v-model:value="form.username" placeholder="Kullanıcı adı" />
          </n-form-item>
        </template>
        <n-form-item v-if="editorType !== 'responsible'" label="Sıra">
          <n-input-number v-model:value="form.order" :min="0" />
        </n-form-item>
        <n-space justify="end">
          <n-button @click="showModal = false">Vazgeç</n-button>
          <n-button
            circle
            attr-type="submit"
            type="primary"
            title="Kaydet"
            aria-label="Kaydet"
            :loading="saving"
            :disabled="!form.name || (editorType === 'project' && !form.code)"
          >
            <template #icon><Save :size="17" /></template>
          </n-button>
        </n-space>
      </n-form>
    </n-modal>
  </section>
</template>
