<script setup>
import { computed, h, reactive, ref } from "vue";
import { NButton, NIcon, NSpace, NTag, NText, NTooltip, useDialog } from "naive-ui";
import {
  AlertTriangle,
  CalendarDays,
  Download,
  ExternalLink,
  FileCheck2,
  FileText,
  Paperclip,
  Pencil,
  Plane,
  Plus,
  RefreshCw,
  Search,
  ShieldCheck,
  Trash2
} from "@lucide/vue";

const props = defineProps({
  permits: { type: Array, required: true },
  loading: { type: Boolean, required: true },
  saving: { type: Boolean, required: true },
  error: { type: String, default: "" },
  notice: { type: String, default: "" }
});

const emit = defineEmits(["refresh", "save", "delete"]);
const dialog = useDialog();

const permitTypes = [
  { label: "Yurt İçi", value: "domestic" },
  { label: "Uluslararası", value: "international" },
  { label: "Test Uçuşu", value: "test" },
  { label: "İntikal Uçuşu", value: "ferry" }
];
const recordStatuses = [
  { label: "Taslak", value: "draft" },
  { label: "Onaylandı", value: "approved" },
  { label: "Askıya Alındı", value: "suspended" },
  { label: "İptal Edildi", value: "revoked" }
];
const validityStatuses = [
  { label: "Geçerli", value: "active" },
  { label: "Süresi Yaklaşıyor", value: "expiring" },
  { label: "Yaklaşan", value: "upcoming" },
  { label: "Süresi Doldu", value: "expired" },
  { label: "Taslak", value: "draft" },
  { label: "Askıya Alındı", value: "suspended" },
  { label: "İptal Edildi", value: "revoked" }
];
const validityTagTypes = {
  active: "success",
  expiring: "warning",
  upcoming: "info",
  expired: "error",
  draft: "default",
  suspended: "warning",
  revoked: "error"
};

const searchTerm = ref("");
const statusFilter = ref(null);
const typeFilter = ref(null);
const aircraftFilter = ref(null);
const showEditor = ref(false);
const editingId = ref(null);
const formError = ref("");
const fileList = ref([]);
const existingDocument = ref(null);
const removeDocument = ref(false);
const form = reactive({
  aircraft_number: "",
  permit_number: "",
  permit_type: "domestic",
  issuing_authority: "",
  flight_region: "",
  valid_from: null,
  valid_until: null,
  status: "approved",
  notes: ""
});

function normalize(value) {
  return (value || "").toLocaleLowerCase("tr-TR").trim();
}

const aircraftOptions = computed(() =>
  [...new Set(props.permits.map((permit) => permit.aircraft_number))]
    .sort((a, b) => a.localeCompare(b, "tr"))
    .map((value) => ({ label: value, value }))
);

const filteredPermits = computed(() => {
  const query = normalize(searchTerm.value);
  return props.permits.filter((permit) => {
    const matchesSearch =
      !query ||
      [
        permit.aircraft_number,
        permit.permit_number,
        permit.issuing_authority,
        permit.flight_region,
        permit.document_name
      ].some((value) => normalize(value).includes(query));
    return (
      matchesSearch &&
      (!statusFilter.value || permit.validity_status === statusFilter.value) &&
      (!typeFilter.value || permit.permit_type === typeFilter.value) &&
      (!aircraftFilter.value || permit.aircraft_number === aircraftFilter.value)
    );
  });
});

const metrics = computed(() => ({
  total: props.permits.length,
  active: props.permits.filter((permit) => permit.validity_status === "active").length,
  expiring: props.permits.filter((permit) => permit.validity_status === "expiring").length,
  expired: props.permits.filter((permit) => permit.validity_status === "expired").length,
  documented: props.permits.filter((permit) => permit.document_url).length
}));

function formatDate(value) {
  if (!value) return "—";
  return new Intl.DateTimeFormat("tr-TR", {
    day: "2-digit",
    month: "short",
    year: "numeric"
  }).format(new Date(`${value}T12:00:00`));
}

function formatFileSize(size) {
  if (!size) return "";
  if (size < 1024 * 1024) return `${Math.ceil(size / 1024)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

function openDocument(permit) {
  if (!permit.document_url) return;
  const opened = window.open(permit.document_url, "_blank", "noopener,noreferrer");
  if (opened) opened.opener = null;
}

function downloadGeneratedPermit(permit) {
  const link = document.createElement("a");
  link.href = permit.generated_document_url;
  link.download = `Ucus_Izni_${permit.aircraft_number}_${permit.permit_number}.docx`;
  document.body.appendChild(link);
  link.click();
  link.remove();
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
            type: options.type,
            disabled: options.disabled,
            "aria-label": title,
            onClick
          },
          { icon: () => h(NIcon, null, { default: () => h(icon, { size: 17 }) }) }
        ),
      default: () => title
    }
  );
}

const tableColumns = [
  {
    title: "Uçak",
    key: "aircraft_number",
    width: 140,
    fixed: "left",
    sorter: (a, b) => a.aircraft_number.localeCompare(b.aircraft_number, "tr"),
    render: (permit) =>
      h(NSpace, { align: "center", size: 8 }, {
        default: () => [
          h(NIcon, { color: "#0f766e", size: 18 }, { default: () => h(Plane) }),
          h(NText, { strong: true }, { default: () => permit.aircraft_number })
        ]
      })
  },
  {
    title: "İzin",
    key: "permit_number",
    width: 210,
    sorter: (a, b) => a.permit_number.localeCompare(b.permit_number, "tr"),
    render: (permit) =>
      h(NSpace, { vertical: true, size: 3 }, {
        default: () => [
          h(NText, { strong: true, type: "primary" }, { default: () => permit.permit_number }),
          h(NText, { depth: 3 }, { default: () => permit.permit_type_display })
        ]
      })
  },
  {
    title: "Yetkili kurum / bölge",
    key: "authority",
    width: 230,
    sorter: (a, b) => a.issuing_authority.localeCompare(b.issuing_authority, "tr"),
    render: (permit) =>
      h(NSpace, { vertical: true, size: 3 }, {
        default: () => [
          h(NText, { strong: true }, { default: () => permit.issuing_authority }),
          h(NText, { depth: 3 }, { default: () => permit.flight_region || "Bölge belirtilmedi" })
        ]
      })
  },
  {
    title: "Geçerlilik",
    key: "valid_until",
    width: 185,
    sorter: (a, b) => a.valid_until.localeCompare(b.valid_until),
    render: (permit) =>
      h(NSpace, { vertical: true, size: 3 }, {
        default: () => [
          h(NText, null, { default: () => formatDate(permit.valid_from) }),
          h(NText, { depth: 3 }, { default: () => `→ ${formatDate(permit.valid_until)}` })
        ]
      })
  },
  {
    title: "Durum",
    key: "validity_status",
    width: 170,
    render: (permit) =>
      h(
        NTag,
        { size: "small", bordered: false, type: validityTagTypes[permit.validity_status] },
        { default: () => permit.validity_status_display }
      )
  },
  {
    title: "Doküman",
    key: "document",
    width: 220,
    render(permit) {
      if (!permit.document_url) {
        return h(NText, { depth: 3 }, { default: () => "Eklenmedi" });
      }
      return h(
        NButton,
        { text: true, type: "primary", onClick: () => openDocument(permit) },
        {
          icon: () => h(NIcon, null, { default: () => h(FileText) }),
          default: () =>
            h(NSpace, { vertical: true, size: 0 }, {
              default: () => [
                h(NText, { class: "fp-file-name", type: "primary" }, { default: () => permit.document_name }),
                h(NText, { depth: 3 }, { default: () => formatFileSize(permit.document_size) })
              ]
            })
        }
      );
    }
  },
  {
    title: "İşlemler",
    key: "actions",
    width: 218,
    fixed: "right",
    align: "right",
    render: (permit) =>
      h(NSpace, { justify: "end", size: 2 }, {
        default: () => [
          h(
            NButton,
            {
              size: "small",
              secondary: true,
              type: "primary",
              onClick: () => downloadGeneratedPermit(permit)
            },
            {
              icon: () => h(NIcon, null, { default: () => h(Download, { size: 16 }) }),
              default: () => "Word indir"
            }
          ),
          iconButton(Pencil, "İzni düzenle", () => openEditor(permit)),
          iconButton(Trash2, "İzni sil", () => requestDelete(permit), { type: "error" })
        ]
      })
  }
];

const tablePagination = {
  pageSize: 10,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
  showQuickJumper: true
};

function resetForm() {
  Object.assign(form, {
    aircraft_number: "",
    permit_number: "",
    permit_type: "domestic",
    issuing_authority: "",
    flight_region: "",
    valid_from: null,
    valid_until: null,
    status: "approved",
    notes: ""
  });
  fileList.value = [];
  existingDocument.value = null;
  removeDocument.value = false;
  formError.value = "";
}

function openEditor(permit = null) {
  resetForm();
  editingId.value = permit?.id ?? null;
  if (permit) {
    Object.assign(form, {
      aircraft_number: permit.aircraft_number,
      permit_number: permit.permit_number,
      permit_type: permit.permit_type,
      issuing_authority: permit.issuing_authority,
      flight_region: permit.flight_region,
      valid_from: permit.valid_from,
      valid_until: permit.valid_until,
      status: permit.status,
      notes: permit.notes
    });
    existingDocument.value = permit.document_url
      ? { name: permit.document_name, url: permit.document_url, size: permit.document_size }
      : null;
  }
  showEditor.value = true;
}

function submitPermit() {
  formError.value = "";
  if (
    !form.aircraft_number.trim() ||
    !form.permit_number.trim() ||
    !form.issuing_authority.trim() ||
    !form.valid_from ||
    !form.valid_until
  ) {
    formError.value = "Uçak numarası, izin numarası, yetkili kurum ve geçerlilik tarihleri zorunludur.";
    return;
  }
  if (form.valid_until < form.valid_from) {
    formError.value = "Geçerlilik bitiş tarihi başlangıç tarihinden önce olamaz.";
    return;
  }
  emit("save", {
    id: editingId.value,
    payload: {
      ...form,
      aircraft_number: form.aircraft_number.trim().toUpperCase(),
      permit_number: form.permit_number.trim().toUpperCase(),
      issuing_authority: form.issuing_authority.trim()
    },
    file: fileList.value[0]?.file || null,
    removeDocument: removeDocument.value,
    done: () => {
      showEditor.value = false;
    }
  });
}

function requestDelete(permit) {
  dialog.warning({
    title: "Uçuş iznini sil",
    content: `“${permit.aircraft_number} — ${permit.permit_number}” kaydı${permit.document_url ? " ve ekli dokümanı" : ""} kalıcı olarak silinecek.`,
    positiveText: "Sil",
    negativeText: "Vazgeç",
    positiveButtonProps: { type: "error" },
    onPositiveClick: () => emit("delete", permit)
  });
}

function markDocumentForRemoval() {
  existingDocument.value = null;
  removeDocument.value = true;
}

function updateFileList(files) {
  fileList.value = files.slice(-1);
  if (fileList.value.length) removeDocument.value = false;
}
</script>

<template>
  <section class="flight-permits-view">
    <n-page-header
      title="Uçuş İzinleri"
      subtitle="Uçak bazlı izinleri, geçerlilik sürelerini ve resmi dokümanlarını tek merkezden yönetin."
    >
      <template #header>
        <n-space align="center" :size="6">
          <n-icon :size="16"><Plane /></n-icon>
          <n-text type="primary" strong>Uçuş Operasyonları</n-text>
        </n-space>
      </template>
      <template #extra>
        <n-space>
          <n-button secondary :loading="loading" @click="emit('refresh')">
            <template #icon><n-icon><RefreshCw /></n-icon></template>
            Yenile
          </n-button>
          <n-button type="primary" @click="openEditor()">
            <template #icon><n-icon><Plus /></n-icon></template>
            Yeni uçuş izni
          </n-button>
        </n-space>
      </template>
    </n-page-header>

    <n-alert v-if="error" type="error" title="Uçuş izinleri alınamadı">{{ error }}</n-alert>
    <n-alert v-if="notice" type="success" :show-icon="true">{{ notice }}</n-alert>

    <n-grid cols="1 s:2 m:3 l:5" responsive="screen" :x-gap="12" :y-gap="12">
      <n-grid-item>
        <n-card size="small" class="fp-metric fp-metric-primary">
          <n-statistic label="Toplam izin" :value="metrics.total">
            <template #prefix><n-icon><FileCheck2 /></n-icon></template>
          </n-statistic>
          <n-text :depth="3">Tüm uçaklar</n-text>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card size="small" class="fp-metric">
          <n-statistic label="Geçerli" :value="metrics.active">
            <template #prefix><n-icon><ShieldCheck /></n-icon></template>
          </n-statistic>
          <n-text :depth="3">30 günden uzun</n-text>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card size="small" class="fp-metric fp-metric-warning">
          <n-statistic label="Süresi yaklaşan" :value="metrics.expiring">
            <template #prefix><n-icon><CalendarDays /></n-icon></template>
          </n-statistic>
          <n-text :depth="3">Son 30 gün</n-text>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card size="small" class="fp-metric fp-metric-danger">
          <n-statistic label="Süresi dolan" :value="metrics.expired">
            <template #prefix><n-icon><AlertTriangle /></n-icon></template>
          </n-statistic>
          <n-text :depth="3">Yenileme gerekli</n-text>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card size="small" class="fp-metric">
          <n-statistic label="Dokümanlı" :value="metrics.documented">
            <template #prefix><n-icon><Paperclip /></n-icon></template>
          </n-statistic>
          <n-text :depth="3">Dosyası ekli</n-text>
        </n-card>
      </n-grid-item>
    </n-grid>

    <n-card class="fp-table-card" content-style="padding: 0">
      <n-grid class="fp-filter-bar" cols="1 s:2 l:4" responsive="screen" :x-gap="10" :y-gap="10">
        <n-grid-item>
          <n-input v-model:value="searchTerm" clearable placeholder="Uçak, izin no, kurum veya bölge ara…">
            <template #prefix><n-icon><Search /></n-icon></template>
          </n-input>
        </n-grid-item>
        <n-grid-item>
          <n-select v-model:value="statusFilter" clearable placeholder="Tüm durumlar" :options="validityStatuses" />
        </n-grid-item>
        <n-grid-item>
          <n-select v-model:value="typeFilter" clearable placeholder="Tüm izin türleri" :options="permitTypes" />
        </n-grid-item>
        <n-grid-item>
          <n-select v-model:value="aircraftFilter" clearable filterable placeholder="Tüm uçaklar" :options="aircraftOptions" />
        </n-grid-item>
      </n-grid>

      <n-flex class="fp-table-summary" justify="space-between" align="center">
        <n-text strong>{{ filteredPermits.length }} uçuş izni</n-text>
        <n-text :depth="3">Güncel geçerlilik durumuna göre hesaplanır</n-text>
      </n-flex>

      <n-data-table
        class="fp-data-table"
        :columns="tableColumns"
        :data="filteredPermits"
        :loading="loading"
        :pagination="tablePagination"
        :row-key="(permit) => permit.id"
        :scroll-x="1333"
      />
    </n-card>

    <n-modal v-model:show="showEditor" preset="card" class="fp-editor-modal" :title="editingId ? 'Uçuş iznini düzenle' : 'Yeni uçuş izni'" :bordered="false">
      <n-alert v-if="formError" type="error" class="fp-form-alert">{{ formError }}</n-alert>
      <n-form label-placement="top">
        <n-grid cols="1 s:2" responsive="screen" :x-gap="16">
          <n-form-item-gi label="Uçak numarası" required>
            <n-input v-model:value="form.aircraft_number" placeholder="Örn. TC-UAV-104" />
          </n-form-item-gi>
          <n-form-item-gi label="Uçuş izin numarası" required>
            <n-input v-model:value="form.permit_number" placeholder="Örn. SHGM-UI-2026-0042" />
          </n-form-item-gi>
          <n-form-item-gi label="İzin türü" required>
            <n-select v-model:value="form.permit_type" :options="permitTypes" />
          </n-form-item-gi>
          <n-form-item-gi label="Kayıt durumu" required>
            <n-select v-model:value="form.status" :options="recordStatuses" />
          </n-form-item-gi>
          <n-form-item-gi label="İzni veren kurum" required>
            <n-input v-model:value="form.issuing_authority" placeholder="Örn. SHGM" />
          </n-form-item-gi>
          <n-form-item-gi label="Uçuş bölgesi / kapsam">
            <n-input v-model:value="form.flight_region" placeholder="Örn. Ankara FIR / Test Sahası A" />
          </n-form-item-gi>
          <n-form-item-gi label="Geçerlilik başlangıcı" required>
            <n-date-picker v-model:formatted-value="form.valid_from" value-format="yyyy-MM-dd" type="date" clearable />
          </n-form-item-gi>
          <n-form-item-gi label="Geçerlilik bitişi" required>
            <n-date-picker v-model:formatted-value="form.valid_until" value-format="yyyy-MM-dd" type="date" clearable />
          </n-form-item-gi>
        </n-grid>

        <n-form-item label="Notlar">
          <n-input v-model:value="form.notes" type="textarea" :rows="3" placeholder="Operasyon koşulları veya ek açıklamalar…" />
        </n-form-item>

        <n-form-item label="İzin dokümanı">
          <div class="fp-upload-area">
            <n-alert v-if="existingDocument" type="info" :show-icon="false">
              <n-flex justify="space-between" align="center">
                <n-button text type="primary" @click="openDocument({ document_url: existingDocument.url })">
                  <template #icon><n-icon><ExternalLink /></n-icon></template>
                  {{ existingDocument.name }} · {{ formatFileSize(existingDocument.size) }}
                </n-button>
                <n-button text type="error" @click="markDocumentForRemoval">Kaldır</n-button>
              </n-flex>
            </n-alert>
            <n-upload
              :file-list="fileList"
              :default-upload="false"
              :max="1"
              accept=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png"
              @update:file-list="updateFileList"
            >
              <n-upload-dragger>
                <n-icon :size="32" :depth="3"><Paperclip /></n-icon>
                <n-text class="fp-upload-title">Dokümanı buraya bırakın veya seçin</n-text>
                <n-text :depth="3">PDF, Office belgesi veya görsel · en fazla 15 MB</n-text>
              </n-upload-dragger>
            </n-upload>
          </div>
        </n-form-item>
      </n-form>
      <template #footer>
        <n-flex justify="end">
          <n-button @click="showEditor = false">Vazgeç</n-button>
          <n-button type="primary" :loading="saving" @click="submitPermit">Kaydet</n-button>
        </n-flex>
      </template>
    </n-modal>
  </section>
</template>
