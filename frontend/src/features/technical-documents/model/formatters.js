const DATE_FORMATTER = new Intl.DateTimeFormat("tr-TR", {
  day: "2-digit",
  month: "short",
  year: "numeric"
});

const DATE_TIME_FORMATTER = new Intl.DateTimeFormat("tr-TR", {
  day: "2-digit",
  month: "short",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit"
});

export function isoDateKey(date = new Date()) {
  return date.toISOString().slice(0, 10);
}

export function formatTechnicalDocumentDate(value) {
  if (!value) return "—";
  return DATE_FORMATTER.format(new Date(`${value}T12:00:00`));
}

export function formatTechnicalDocumentDateTime(value) {
  if (!value) return "—";
  return DATE_TIME_FORMATTER.format(new Date(value));
}
