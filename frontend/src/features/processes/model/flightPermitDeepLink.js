function firstQueryValue(value) {
  return Array.isArray(value) ? value[0] : value;
}

export function resolveFlightPermitDeepLink(queryValue, records = []) {
  if (queryValue == null) return { record: null, error: "" };

  const rawValue = firstQueryValue(queryValue);
  if (!/^\d+$/.test(String(rawValue || "")) || Number(rawValue) <= 0) {
    return {
      record: null,
      error: "Uçuş izni bağlantısı geçersiz. Normal süreç listesi gösteriliyor."
    };
  }

  const id = Number(rawValue);
  const record = records.find((item) => item.id === id && item.process_code === "flight-permits");
  if (!record) {
    return {
      record: null,
      error:
        "İstenen uçuş izni bulunamadı veya bu kaydı görüntüleme yetkiniz yok. Normal süreç listesi gösteriliyor."
    };
  }
  return { record, error: "" };
}
