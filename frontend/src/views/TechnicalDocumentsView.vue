<script setup>
import { computed, h, reactive, ref, watch } from "vue";
import {
  NButton,
  NIcon,
  NSelect,
  NSpace,
  NTag,
  NText,
  NThing,
  NTooltip,
  useDialog
} from "naive-ui";
import {
  AlertTriangle,
  BellRing,
  CalendarClock,
  CheckCircle2,
  Eye,
  FileCheck2,
  FileText,
  Mail,
  Pencil,
  Plus,
  RefreshCw,
  Search,
  Send,
  Trash2
} from "@lucide/vue";

const props = defineProps({
  projects: { type: Array, required: true },
  documents: { type: Array, required: true },
  loading: { type: Boolean, required: true },
  saving: { type: Boolean, required: true },
  notifyingId: { type: Number, default: null },
  error: { type: String, default: "" },
  notice: { type: String, default: "" },
  canEdit: { type: Boolean, default: false }
});

const emit = defineEmits(["refresh", "save", "delete", "notify"]);
const dialog = useDialog();

const statuses = [
  { label: "Taslak", value: "draft" },
  { label: "İncelemede", value: "in_review" },
  { label: "Revizyon Bekliyor", value: "changes_requested" },
  { label: "Onaylandı", value: "approved" },
  { label: "Yayınlandı", value: "published" },
  { label: "Yürürlükten Kalktı", value: "superseded" },
  { label: "Arşivlendi", value: "archived" }
];

const statusTypes = {
  draft: "default",
  in_review: "info",
  changes_requested: "warning",
  approved: "success",
  published: "success",
  superseded: "error",
  archived: "default"
};

const priorityTypes = {
  normal: "default",
  high: "warning",
  critical: "error"
};

const activeProjectId = ref(null);
const searchTerm = ref("");
const statusFilter = ref(null);
const panelFilter = ref(null);
const categoryFilter = ref(null);
const showEditor = ref(false);
const showDetail = ref(false);
const showNotify = ref(false);
const editingId = ref(null);
const detailDocument = ref(null);
const notifyDocument = ref(null);
const formError = ref("");
const notifyForm = reactive({ subject: "", message: "" });
const form = reactive({
  project: null,
  panels: [],
  code: "",
  title: "",
  description: "",
  category: "",
  document_type: "",
  revision: "A",
  status: "draft",
  priority: "normal",
  classification: "internal",
  owner_name: "",
  publication_date: null,
  due_date: null,
  review_date: null,
  source_url: "",
  notes: ""
});

watch(
  () => props.projects,
  (projects) => {
    if (!projects.length) {
      activeProjectId.value = null;
      return;
    }
    if (!projects.some((project) => project.id === activeProjectId.value)) {
      activeProjectId.value = projects[0].id;
    }
  },
  { immediate: true }
);

const activeProject = computed(
  () => props.projects.find((project) => project.id === activeProjectId.value) || null
);
const projectDocuments = computed(() =>
  props.documents.filter((document) => document.project === activeProjectId.value)
);
const activePanels = computed(() => activeProject.value?.panels || []);
const panelOptions = computed(() =>
  activePanels.value.map((panel) => ({ label: panel.name, value: panel.id }))
);
const categoryOptions = computed(() =>
  [...new Set(projectDocuments.value.map((document) => document.category).filter(Boolean))]
    .sort()
    .map((category) => ({ label: category, value: category }))
);

function normalizedSearch(value) {
  return (value || "").toLocaleLowerCase("tr-TR").trim();
}

const filteredDocuments = computed(() => {
  const query = normalizedSearch(searchTerm.value);
  return projectDocuments.value.filter((document) => {
    const matchesSearch =
      !query ||
      [document.code, document.title, document.owner_name, document.category].some((value) =>
        normalizedSearch(value).includes(query)
      );
    const matchesStatus = !statusFilter.value || document.status === statusFilter.value;
    const matchesPanel =
      !panelFilter.value ||
      document.panel_details.some((panel) => panel.id === panelFilter.value);
    const matchesCategory = !categoryFilter.value || document.category === categoryFilter.value;
    return matchesSearch && matchesStatus && matchesPanel && matchesCategory;
  });
});

const today = new Date().toISOString().slice(0, 10);
function isOverdue(document) {
  return (
    document.due_date &&
    document.due_date < today &&
    !["published", "superseded", "archived"].includes(document.status)
  );
}

const metrics = computed(() => {
  const documents = projectDocuments.value;
  const published = documents.filter((document) => document.status === "published").length;
  const active = documents.filter((document) =>
    ["in_review", "changes_requested", "approved"].includes(document.status)
  ).length;
  const overdue = documents.filter(isOverdue).length;
  const notified = documents.filter((document) => document.last_notification_at).length;
  return {
    total: documents.length,
    published,
    active,
    overdue,
    notified,
    publicationRate: documents.length ? Math.round((published / documents.length) * 100) : 0
  };
});

function projectDocumentCount(projectId) {
  return props.documents.filter((document) => document.project === projectId).length;
}

function formatDate(value) {
  if (!value) return "—";
  return new Intl.DateTimeFormat("tr-TR", {
    day: "2-digit",
    month: "short",
    year: "numeric"
  }).format(new Date(`${value}T12:00:00`));
}

function formatDateTime(value) {
  if (!value) return "—";
  return new Intl.DateTimeFormat("tr-TR", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(value));
}

function iconButton(icon, title, onClick, options = {}) {
  return h(
    NTooltip,
    null,
    {
      trigger: () =>
        h(
          NButton,
          {
            circle: true,
            quaternary: true,
            size: "small",
            "aria-label": title,
            type: options.type,
            disabled: options.disabled,
            loading: options.loading,
            onClick
          },
          {
            icon: () =>
              h(NIcon, null, {
                default: () => h(icon, { size: 17 })
              })
          }
        ),
      default: () => title
    },
  );
}

const tableColumns = computed(() => [
  {
    title: "Doküman",
    key: "document",
    width: 290,
    fixed: "left",
    sorter: (a, b) => a.code.localeCompare(b.code, "tr"),
    render(document) {
      const codeRow = [
        h(NText, { strong: true, type: "primary" }, { default: () => document.code }),
        document.priority !== "normal"
          ? h(
              NTag,
              { size: "tiny", type: priorityTypes[document.priority] },
              { default: () => document.priority_display }
            )
          : null
      ];
      return h(
        NSpace,
        { class: "td-document-cell", vertical: true, size: 2 },
        {
          default: () => [
            h(NSpace, { size: 6, align: "center" }, { default: () => codeRow }),
            h(
              NButton,
              { text: true, type: "primary", onClick: () => openDetails(document) },
              { default: () => document.title }
            ),
            h(
              NText,
              { depth: 3 },
              { default: () => document.category || document.document_type || "Kategorisiz" }
            )
          ]
        }
      );
    }
  },
  {
    title: "Panel kapsamı",
    key: "panels",
    width: 190,
    render(document) {
      if (!document.panel_details.length) {
        return h(NText, { depth: 3 }, { default: () => "Proje geneli" });
      }
      const tags = document.panel_details
        .slice(0, 2)
        .map((panel) =>
          h(
            NTag,
            { key: panel.id, size: "small", bordered: false },
            { default: () => panel.name }
          )
        );
      if (document.panel_details.length > 2) {
        tags.push(
          h(
            NTag,
            { key: "remaining", size: "small" },
            { default: () => `+${document.panel_details.length - 2}` }
          )
        );
      }
      return h(NSpace, { size: 4, wrap: true }, { default: () => tags });
    }
  },
  {
    title: "Durum",
    key: "status",
    width: 175,
    sorter: (a, b) =>
      statuses.findIndex((status) => status.value === a.status) -
      statuses.findIndex((status) => status.value === b.status),
    render(document) {
      if (!props.canEdit) {
        return h(
          NTag,
          { size: "small", type: statusTypes[document.status] },
          { default: () => document.status_display }
        );
      }
      return h(NSelect, {
        class: "td-status-select",
        size: "small",
        value: document.status,
        options: statuses,
        "onUpdate:value": (value) => updateStatus(document, value)
      });
    }
  },
  {
    title: "Rev.",
    key: "revision",
    width: 75,
    sorter: "default",
    render: (document) =>
      h(NText, { strong: true }, { default: () => document.revision })
  },
  {
    title: "Yayın / termin",
    key: "dates",
    width: 170,
    sorter: (a, b) => (a.due_date || "9999").localeCompare(b.due_date || "9999"),
    render(document) {
      return h(
        NSpace,
        { class: "td-date-stack", vertical: true, size: 2 },
        {
          default: () => [
            h(
              NText,
              { depth: 3 },
              { default: () => `Yayın · ${formatDate(document.publication_date)}` }
            ),
            h(
              NText,
              { type: isOverdue(document) ? "error" : "default", strong: isOverdue(document) },
              { default: () => `Termin · ${formatDate(document.due_date)}` }
            )
          ]
        }
      );
    }
  },
  {
    title: "Sorumlu",
    key: "owner_name",
    width: 190,
    sorter: (a, b) => (a.owner_name || "").localeCompare(b.owner_name || "", "tr"),
    render(document) {
      return h(NThing, {
        title: document.owner_name || "Atanmamış",
        description: document.last_notification_at
          ? `Son bildirim ${formatDateTime(document.last_notification_at)}`
          : "Bildirim gönderilmedi"
      });
    }
  },
  {
    title: "İşlemler",
    key: "actions",
    width: props.canEdit ? 166 : 88,
    fixed: "right",
    align: "right",
    render(document) {
      const actions = [
        iconButton(Eye, "Detayı görüntüle", () => openDetails(document)),
        iconButton(
          Mail,
          "Panel sorumlularına e-posta gönder",
          () => openNotification(document),
          {
            type: "primary",
            disabled: !document.notification_recipients.length,
            loading: props.notifyingId === document.id
          }
        )
      ];
      if (props.canEdit) {
        actions.push(
          iconButton(Pencil, "Dokümanı düzenle", () => openEditor(document)),
          iconButton(Trash2, "Dokümanı sil", () => requestDelete(document), {
            type: "error"
          })
        );
      }
      return h(NSpace, { justify: "end", size: 2 }, { default: () => actions });
    }
  }
]);

const tablePagination = {
  pageSize: 10,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
  showQuickJumper: true
};

function selectProject(projectId) {
  activeProjectId.value = projectId;
  searchTerm.value = "";
  statusFilter.value = null;
  panelFilter.value = null;
  categoryFilter.value = null;
}

function resetForm() {
  Object.assign(form, {
    project: activeProjectId.value,
    panels: [],
    code: "",
    title: "",
    description: "",
    category: "",
    document_type: "",
    revision: "A",
    status: "draft",
    priority: "normal",
    classification: "internal",
    owner_name: "",
    publication_date: null,
    due_date: null,
    review_date: null,
    source_url: "",
    notes: ""
  });
  formError.value = "";
}

function openEditor(document = null) {
  resetForm();
  editingId.value = document?.id ?? null;
  if (document) {
    Object.assign(form, {
      project: document.project,
      panels: document.panel_details.map((panel) => panel.id),
      code: document.code,
      title: document.title,
      description: document.description,
      category: document.category,
      document_type: document.document_type,
      revision: document.revision,
      status: document.status,
      priority: document.priority,
      classification: document.classification,
      owner_name: document.owner_name,
      publication_date: document.publication_date,
      due_date: document.due_date,
      review_date: document.review_date,
      source_url: document.source_url,
      notes: document.notes
    });
  }
  showEditor.value = true;
}

function submitDocument() {
  formError.value = "";
  if (!form.project || !form.code.trim() || !form.title.trim()) {
    formError.value = "Proje, doküman kodu ve başlık zorunludur.";
    return;
  }
  if (form.status === "published" && !form.publication_date) {
    formError.value = "Yayınlanan doküman için yayın tarihi zorunludur.";
    return;
  }
  emit("save", {
    id: editingId.value,
    payload: {
      ...form,
      code: form.code.trim(),
      title: form.title.trim(),
      publication_date: form.publication_date || null,
      due_date: form.due_date || null,
      review_date: form.review_date || null
    },
    done: () => {
      showEditor.value = false;
    }
  });
}

function requestDelete(document) {
  dialog.warning({
    title: "Teknik dokümanı sil",
    content: `“${document.code} — ${document.title}” dokümanı ve denetim geçmişi silinecek.`,
    positiveText: "Sil",
    negativeText: "Vazgeç",
    positiveButtonProps: { type: "error" },
    onPositiveClick: () => emit("delete", document)
  });
}

function openDetails(document) {
  detailDocument.value = document;
  showDetail.value = true;
}

function openNotification(document) {
  notifyDocument.value = document;
  notifyForm.subject = `[${document.project_code}] ${document.code} — ${document.title}`;
  notifyForm.message =
    `${document.code} kodlu “${document.title}” dokümanı için bilgilendirme.\n\n` +
    `Durum: ${document.status_display}\nRevizyon: ${document.revision}\n` +
    `Yayın tarihi: ${formatDate(document.publication_date)}\nTermin: ${formatDate(document.due_date)}`;
  showNotify.value = true;
}

function submitNotification() {
  if (!notifyDocument.value) return;
  emit("notify", {
    document: notifyDocument.value,
    payload: { ...notifyForm },
    done: () => {
      showNotify.value = false;
    }
  });
}

function updateStatus(document, status) {
  if (status === document.status) return;
  if (status === "published" && !document.publication_date) {
    openEditor({ ...document, status: "published", publication_date: today });
    return;
  }
  emit("save", {
    id: document.id,
    payload: { status, status_note: "Doküman tablosundan durum güncellendi." }
  });
}
</script>

<template>
  <section class="technical-documents-view">
    <n-page-header
      class="td-page-header"
      title="Teknik Dokümanlar"
      subtitle="Yayın, revizyon ve panel sorumluluklarını proje bazında tek merkezden takip edin."
    >
      <template #header>
        <n-space align="center" :size="6">
          <n-icon :size="15"><FileText /></n-icon>
          <n-text type="primary" strong>Doküman Yönetimi</n-text>
        </n-space>
      </template>
      <template #extra>
        <n-space>
          <n-button secondary :loading="loading" @click="emit('refresh')">
            <template #icon><n-icon><RefreshCw /></n-icon></template>
            Yenile
          </n-button>
          <n-button v-if="canEdit" type="primary" :disabled="!activeProject" @click="openEditor()">
            <template #icon><n-icon><Plus /></n-icon></template>
            Yeni doküman
          </n-button>
        </n-space>
      </template>
    </n-page-header>

    <n-alert v-if="error" type="error" title="Teknik dokümanlar alınamadı">{{ error }}</n-alert>
    <n-alert v-if="notice" type="success" :show-icon="true">{{ notice }}</n-alert>

    <n-empty
      v-if="!projects.length"
      description="Önce Organizasyon Yönetimi alanından bir proje oluşturun."
    />

    <template v-else>
      <n-tabs
        class="td-project-tabs"
        type="segment"
        :value="activeProjectId"
        @update:value="selectProject"
      >
        <n-tab v-for="project in projects" :key="project.id" :name="project.id">
          <n-space align="center" :size="8">
            <n-tag size="small" type="primary" :bordered="false">{{ project.code }}</n-tag>
            <n-text strong>{{ project.name }}</n-text>
            <n-badge :value="projectDocumentCount(project.id)" :max="99" />
          </n-space>
        </n-tab>
      </n-tabs>

      <n-spin :show="loading">
        <n-grid
          class="td-metric-grid"
          cols="1 s:2 m:3 l:5"
          responsive="screen"
          :x-gap="12"
          :y-gap="12"
        >
          <n-grid-item>
            <n-card size="small" class="td-metric-card td-metric-card-primary">
              <n-statistic label="Toplam doküman" :value="metrics.total">
                <template #prefix><n-icon><FileCheck2 /></n-icon></template>
              </n-statistic>
              <n-text :depth="3">{{ activeProject?.code }} kapsamı</n-text>
            </n-card>
          </n-grid-item>
          <n-grid-item>
            <n-card size="small" class="td-metric-card">
              <n-statistic label="Yayınlanan" :value="metrics.published">
                <template #prefix><n-icon><CheckCircle2 /></n-icon></template>
              </n-statistic>
              <n-progress
                type="line"
                status="success"
                :percentage="metrics.publicationRate"
                :height="5"
                :show-indicator="false"
              />
            </n-card>
          </n-grid-item>
          <n-grid-item>
            <n-card size="small" class="td-metric-card">
              <n-statistic label="Aktif iş akışı" :value="metrics.active">
                <template #prefix><n-icon><CalendarClock /></n-icon></template>
              </n-statistic>
              <n-text :depth="3">İnceleme ve onay</n-text>
            </n-card>
          </n-grid-item>
          <n-grid-item>
            <n-card
              size="small"
              class="td-metric-card"
              :class="{ 'td-metric-card-danger': metrics.overdue }"
            >
              <n-statistic label="Geciken" :value="metrics.overdue">
                <template #prefix><n-icon><AlertTriangle /></n-icon></template>
              </n-statistic>
              <n-text :type="metrics.overdue ? 'error' : 'default'" :depth="3">Termin aşımı</n-text>
            </n-card>
          </n-grid-item>
          <n-grid-item>
            <n-card size="small" class="td-metric-card">
              <n-statistic label="Bilgilendirilen" :value="metrics.notified">
                <template #prefix><n-icon><BellRing /></n-icon></template>
              </n-statistic>
              <n-text :depth="3">En az bir bildirim</n-text>
            </n-card>
          </n-grid-item>
        </n-grid>

        <n-card class="td-table-card" content-style="padding: 0">
          <n-grid
            class="td-table-toolbar"
            cols="1 s:2 l:4"
            responsive="screen"
            :x-gap="10"
            :y-gap="10"
          >
            <n-grid-item>
              <n-input
                v-model:value="searchTerm"
                clearable
                placeholder="Kod, başlık, kategori veya sorumlu ara…"
              >
                <template #prefix><n-icon><Search /></n-icon></template>
              </n-input>
            </n-grid-item>
            <n-grid-item>
              <n-select
                v-model:value="statusFilter"
                clearable
                placeholder="Tüm durumlar"
                :options="statuses"
              />
            </n-grid-item>
            <n-grid-item>
              <n-select
                v-model:value="panelFilter"
                clearable
                placeholder="Tüm paneller"
                :options="panelOptions"
              />
            </n-grid-item>
            <n-grid-item>
              <n-select
                v-model:value="categoryFilter"
                clearable
                placeholder="Tüm kategoriler"
                :options="categoryOptions"
              />
            </n-grid-item>
          </n-grid>

          <n-flex class="td-table-summary" justify="space-between" align="center">
            <n-text strong>{{ filteredDocuments.length }} doküman</n-text>
            <n-tag size="small" :bordered="false">{{ activeProject?.name }} proje kayıtları</n-tag>
          </n-flex>

          <n-data-table
            class="td-data-table"
            :columns="tableColumns"
            :data="filteredDocuments"
            :loading="loading"
            :pagination="tablePagination"
            :row-key="(document) => document.id"
            :scroll-x="1256"
            striped
          />
        </n-card>
      </n-spin>
    </template>

    <n-modal
      v-model:show="showEditor"
      preset="card"
      :title="editingId ? 'Teknik dokümanı düzenle' : 'Yeni teknik doküman'"
      class="td-editor-modal"
    >
      <n-form label-placement="top" @submit.prevent="submitDocument">
        <n-grid cols="1 m:2" responsive="screen" item-responsive :x-gap="18">
          <n-grid-item>
            <n-form-item label="Proje" required>
              <n-select
                v-model:value="form.project"
                :disabled="Boolean(editingId)"
                :options="projects.map((project) => ({ label: `${project.code} — ${project.name}`, value: project.id }))"
              />
            </n-form-item>
          </n-grid-item>
          <n-grid-item>
            <n-form-item label="İlgili paneller">
              <n-select
                v-model:value="form.panels"
                multiple
                clearable
                placeholder="Bir veya daha fazla panel seçin"
                :options="panelOptions"
              />
            </n-form-item>
          </n-grid-item>
          <n-grid-item>
            <n-form-item label="Doküman kodu" required>
              <n-input v-model:value="form.code" placeholder="TPL-SYS-001" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item>
            <n-form-item label="Revizyon" required>
              <n-input v-model:value="form.revision" placeholder="A, B.1, 02…" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item span="1 m:2">
            <n-form-item label="Başlık" required>
              <n-input v-model:value="form.title" placeholder="Dokümanın resmi başlığı" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item>
            <n-form-item label="Kategori">
              <n-input v-model:value="form.category" placeholder="Sistem Mühendisliği" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item>
            <n-form-item label="Doküman tipi">
              <n-input v-model:value="form.document_type" placeholder="Gereksinim, ICD, prosedür…" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item>
            <n-form-item label="Durum">
              <n-select v-model:value="form.status" :options="statuses" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item>
            <n-form-item label="Öncelik">
              <n-select
                v-model:value="form.priority"
                :options="[
                  { label: 'Normal', value: 'normal' },
                  { label: 'Yüksek', value: 'high' },
                  { label: 'Kritik', value: 'critical' }
                ]"
              />
            </n-form-item>
          </n-grid-item>
          <n-grid-item>
            <n-form-item label="Bilgi sınıfı">
              <n-select
                v-model:value="form.classification"
                :options="[
                  { label: 'Kurum İçi', value: 'internal' },
                  { label: 'Gizli', value: 'confidential' },
                  { label: 'Kısıtlı', value: 'restricted' },
                  { label: 'Herkese Açık', value: 'public' }
                ]"
              />
            </n-form-item>
          </n-grid-item>
          <n-grid-item>
            <n-form-item label="Doküman sorumlusu">
              <n-input v-model:value="form.owner_name" placeholder="Ekip veya kişi" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item>
            <n-form-item label="Yayın tarihi">
              <n-date-picker
                v-model:formatted-value="form.publication_date"
                type="date"
                value-format="yyyy-MM-dd"
                clearable
              />
            </n-form-item>
          </n-grid-item>
          <n-grid-item>
            <n-form-item label="Termin">
              <n-date-picker
                v-model:formatted-value="form.due_date"
                type="date"
                value-format="yyyy-MM-dd"
                clearable
              />
            </n-form-item>
          </n-grid-item>
          <n-grid-item>
            <n-form-item label="Sonraki gözden geçirme">
              <n-date-picker
                v-model:formatted-value="form.review_date"
                type="date"
                value-format="yyyy-MM-dd"
                clearable
              />
            </n-form-item>
          </n-grid-item>
          <n-grid-item>
            <n-form-item label="Kaynak bağlantısı">
              <n-input v-model:value="form.source_url" placeholder="https://…" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item span="1 m:2">
            <n-form-item label="Açıklama">
              <n-input v-model:value="form.description" type="textarea" :rows="3" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item span="1 m:2">
            <n-form-item label="Notlar">
              <n-input v-model:value="form.notes" type="textarea" :rows="2" />
            </n-form-item>
          </n-grid-item>
        </n-grid>
        <n-alert v-if="formError" type="error" :show-icon="true">{{ formError }}</n-alert>
        <n-divider />
        <n-flex justify="end">
          <n-button @click="showEditor = false">Vazgeç</n-button>
          <n-button attr-type="submit" type="primary" :loading="saving">
            {{ editingId ? "Değişiklikleri kaydet" : "Dokümanı oluştur" }}
          </n-button>
        </n-flex>
      </n-form>
    </n-modal>

    <n-drawer v-model:show="showDetail" :width="620">
      <n-drawer-content v-if="detailDocument" :title="detailDocument.code" closable>
        <n-thing
          class="td-detail-heading"
          :title="detailDocument.title"
          :description="detailDocument.description || 'Açıklama girilmemiş.'"
        >
          <template #header-extra>
            <n-space>
            <n-tag :type="statusTypes[detailDocument.status]">{{ detailDocument.status_display }}</n-tag>
            <n-tag :bordered="false">Rev. {{ detailDocument.revision }}</n-tag>
            </n-space>
          </template>
        </n-thing>
        <n-descriptions :column="2" bordered label-placement="top">
          <n-descriptions-item label="Proje">{{ detailDocument.project_name }}</n-descriptions-item>
          <n-descriptions-item label="Sorumlu">{{ detailDocument.owner_name || "—" }}</n-descriptions-item>
          <n-descriptions-item label="Kategori">{{ detailDocument.category || "—" }}</n-descriptions-item>
          <n-descriptions-item label="Tip">{{ detailDocument.document_type || "—" }}</n-descriptions-item>
          <n-descriptions-item label="Yayın tarihi">{{ formatDate(detailDocument.publication_date) }}</n-descriptions-item>
          <n-descriptions-item label="Termin">{{ formatDate(detailDocument.due_date) }}</n-descriptions-item>
          <n-descriptions-item label="Bilgi sınıfı">{{ detailDocument.classification_display }}</n-descriptions-item>
          <n-descriptions-item label="Son güncelleme">{{ formatDateTime(detailDocument.updated_at) }}</n-descriptions-item>
        </n-descriptions>

        <n-divider title-placement="left">
          <n-space align="center">
            <n-text strong>Panel kapsamı</n-text>
            <n-badge :value="detailDocument.panel_details.length" />
          </n-space>
        </n-divider>
        <section>
          <n-space v-if="detailDocument.panel_details.length">
            <n-tag v-for="panel in detailDocument.panel_details" :key="panel.id">
              {{ panel.name }} · {{ panel.responsible_count }} sorumlu
            </n-tag>
          </n-space>
          <n-text v-else :depth="3">Bu doküman proje genelini kapsıyor.</n-text>
        </section>

        <n-divider title-placement="left">
          <n-space align="center">
            <n-text strong>Durum geçmişi</n-text>
            <n-badge :value="detailDocument.status_history.length" />
          </n-space>
        </n-divider>
        <section>
          <n-timeline v-if="detailDocument.status_history.length">
            <n-timeline-item
              v-for="history in detailDocument.status_history"
              :key="history.id"
              :type="history.to_status === 'published' ? 'success' : 'info'"
              :title="history.to_status_display"
              :content="history.note || 'Durum güncellendi.'"
              :time="`${formatDateTime(history.created_at)} · ${history.changed_by_name || 'Sistem'}`"
            />
          </n-timeline>
          <n-text v-else :depth="3">Durum hareketi bulunmuyor.</n-text>
        </section>

        <n-divider title-placement="left">
          <n-space align="center">
            <n-text strong>Bildirim geçmişi</n-text>
            <n-badge :value="detailDocument.notifications.length" />
          </n-space>
        </n-divider>
        <section>
          <n-list v-if="detailDocument.notifications.length" bordered>
            <n-list-item
              v-for="notification in detailDocument.notifications"
              :key="notification.id"
            >
              <template #prefix><n-icon><Mail /></n-icon></template>
              <n-thing
                :title="notification.subject"
                :description="`${notification.recipient_count} alıcı · ${formatDateTime(notification.created_at)}`"
              />
              <template #suffix>
                <n-tag size="small" :type="notification.status === 'sent' ? 'success' : 'error'">
                  {{ notification.status === "sent" ? "Gönderildi" : "Başarısız" }}
                </n-tag>
              </template>
            </n-list-item>
          </n-list>
          <n-text v-else :depth="3">Henüz bildirim gönderilmedi.</n-text>
        </section>
      </n-drawer-content>
    </n-drawer>

    <n-modal v-model:show="showNotify" preset="card" title="Panel sorumlularını bilgilendir" class="td-notify-modal">
      <template v-if="notifyDocument">
        <n-alert
          class="td-recipient-box"
          type="info"
          :title="`${notifyDocument.notification_recipients.length} panel sorumlusu`"
        >
          <n-text>
            {{
              notifyDocument.notification_recipients
                .map((recipient) => `${recipient.name} · ${recipient.panel}`)
                .join(", ")
            }}
          </n-text>
        </n-alert>
        <n-form label-placement="top" @submit.prevent="submitNotification">
          <n-form-item label="Konu">
            <n-input v-model:value="notifyForm.subject" />
          </n-form-item>
          <n-form-item label="Mesaj">
            <n-input v-model:value="notifyForm.message" type="textarea" :rows="8" />
          </n-form-item>
          <n-divider />
          <n-flex justify="end">
            <n-button @click="showNotify = false">Vazgeç</n-button>
            <n-button attr-type="submit" type="primary" :loading="notifyingId === notifyDocument.id">
              <template #icon><n-icon><Send /></n-icon></template>
              E-postayı gönder
            </n-button>
          </n-flex>
        </n-form>
      </template>
    </n-modal>
  </section>
</template>
