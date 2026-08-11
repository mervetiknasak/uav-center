const DATE_FORMATTER = new Intl.DateTimeFormat("tr-TR", {
  day: "2-digit",
  month: "short",
  year: "numeric"
});

export function formatFlightPermitDate(value) {
  if (!value) return "—";
  return DATE_FORMATTER.format(new Date(`${value}T12:00:00`));
}

export function formatFlightPermitFileSize(size) {
  if (!size) return "";
  if (size < 1024 * 1024) return `${Math.ceil(size / 1024)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}
