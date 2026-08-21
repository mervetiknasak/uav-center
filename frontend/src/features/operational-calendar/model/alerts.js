export const OPERATIONAL_ALERT_SOURCES = [
  { label: "Teknik doküman", value: "technical_document" },
  { label: "Uçuş izni", value: "flight_permit" }
];

export const OPERATIONAL_ALERT_BUCKETS = [
  { label: "Gecikmiş", value: "overdue" },
  { label: "7 gün içinde", value: "next_7_days" },
  { label: "30 gün içinde", value: "next_30_days" },
  { label: "Bekleyen", value: "stale" }
];

export const OPERATIONAL_ALERT_BUCKET_LABELS = Object.fromEntries(
  OPERATIONAL_ALERT_BUCKETS.map(({ label, value }) => [value, label])
);

export const OPERATIONAL_ALERT_BUCKET_TYPES = {
  overdue: "error",
  next_7_days: "warning",
  next_30_days: "info",
  stale: "default"
};

export const OPERATIONAL_ALERT_SOURCE_LABELS = Object.fromEntries(
  OPERATIONAL_ALERT_SOURCES.map(({ label, value }) => [value, label])
);

export const OPERATIONAL_ALERT_TYPE_LABELS = {
  due_date: "Termin tarihi",
  review_date: "İnceleme tarihi",
  workflow_stale: "Bekleyen iş akışı",
  valid_until: "Geçerlilik bitişi"
};

const BUCKET_ORDER = new Map(OPERATIONAL_ALERT_BUCKETS.map(({ value }, index) => [value, index]));

function normalizeSearch(value) {
  return String(value || "")
    .trim()
    .toLocaleLowerCase("tr-TR");
}

function optionSort(left, right) {
  return left.label.localeCompare(right.label, "tr");
}

export function normalizeOperationalAlertsPayload(data) {
  const alerts = Array.isArray(data?.alerts) ? data.alerts : [];
  return {
    as_of: typeof data?.as_of === "string" ? data.as_of : "",
    thresholds: {
      critical_days: Number(data?.thresholds?.critical_days) || 7,
      horizon_days: Number(data?.thresholds?.horizon_days) || 30,
      stale_days: Number(data?.thresholds?.stale_days) || 14
    },
    summary: {
      total: Number(data?.summary?.total) || 0,
      overdue: Number(data?.summary?.overdue) || 0,
      next_7_days: Number(data?.summary?.next_7_days) || 0,
      next_30_days: Number(data?.summary?.next_30_days) || 0,
      stale: Number(data?.summary?.stale) || 0
    },
    alerts
  };
}

export function filterOperationalAlerts(alerts = [], filters = {}) {
  const search = normalizeSearch(filters.search);
  return alerts.filter((alert) => {
    if (filters.sourceType && alert.source_type !== filters.sourceType) return false;
    if (filters.bucket && alert.bucket !== filters.bucket) return false;
    if (filters.projectId && alert.project?.id !== filters.projectId) return false;
    if (filters.panelId && !(alert.panels || []).some((panel) => panel.id === filters.panelId)) {
      return false;
    }
    if (!search) return true;
    return [
      alert.reference,
      alert.title,
      alert.status_display,
      alert.project?.code,
      alert.project?.name,
      ...(alert.panels || []).map((panel) => panel.name)
    ].some((value) => normalizeSearch(value).includes(search));
  });
}

export function sortOperationalAlerts(alerts = []) {
  return [...alerts].sort((left, right) => {
    const bucketDifference =
      (BUCKET_ORDER.get(left.bucket) ?? 99) - (BUCKET_ORDER.get(right.bucket) ?? 99);
    if (bucketDifference) return bucketDifference;

    if (left.bucket === "stale") {
      const staleDifference = (right.days_in_status || 0) - (left.days_in_status || 0);
      if (staleDifference) return staleDifference;
    } else {
      const dateDifference = (left.days_remaining ?? 0) - (right.days_remaining ?? 0);
      if (dateDifference) return dateDifference;
    }
    return String(left.reference || "").localeCompare(String(right.reference || ""), "tr");
  });
}

export function selectOperationalAlertProjects(alerts = []) {
  const projects = new Map();
  for (const alert of alerts) {
    if (alert.project?.id != null) {
      projects.set(alert.project.id, {
        label: `${alert.project.code} — ${alert.project.name}`,
        value: alert.project.id
      });
    }
  }
  return [...projects.values()].sort(optionSort);
}

export function selectOperationalAlertPanels(alerts = [], projectId = null) {
  const panels = new Map();
  for (const alert of alerts) {
    if (projectId && alert.project?.id !== projectId) continue;
    for (const panel of alert.panels || []) {
      panels.set(panel.id, { label: panel.name, value: panel.id });
    }
  }
  return [...panels.values()].sort(optionSort);
}

export function formatOperationalAlertDate(value) {
  if (!value) return "—";
  const [year, month, day] = String(value).split("-").map(Number);
  if (!year || !month || !day) return value;
  return new Intl.DateTimeFormat("tr-TR", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    timeZone: "Europe/Istanbul"
  }).format(new Date(Date.UTC(year, month - 1, day)));
}

export function operationalAlertTimingLabel(alert) {
  if (alert.bucket === "stale") {
    return `${alert.days_in_status || 0} gündür bu durumda`;
  }
  if (alert.days_remaining === 0) return "Bugün";
  if (alert.days_remaining < 0) return `${Math.abs(alert.days_remaining)} gün gecikti`;
  return `${alert.days_remaining} gün kaldı`;
}

export function operationalAlertRoute(alert, action = "open") {
  if (alert.source_type === "technical_document") {
    return {
      name: "technical-documents",
      query: {
        document: String(alert.source_id),
        ...(action === "notify" ? { action: "notify" } : {})
      }
    };
  }
  return {
    name: "processes",
    query: { flightPermit: String(alert.source_id) },
    hash: "#flight-permits"
  };
}
