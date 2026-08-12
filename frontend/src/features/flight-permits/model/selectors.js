export function normalizeFlightPermitSearch(value) {
  return String(value || "")
    .toLocaleLowerCase("tr-TR")
    .trim();
}

export function selectSerialNumberOptions(permits) {
  return [...new Set((permits || []).map((permit) => permit.serial_number).filter(Boolean))]
    .sort((a, b) => a.localeCompare(b, "tr"))
    .map((value) => ({ label: value, value }));
}

export function filterFlightPermits(
  permits,
  { search = "", validityStatus = null, recommendation = null, serialNumber = null } = {}
) {
  const query = normalizeFlightPermitSearch(search);
  return (permits || []).filter((permit) => {
    const matchesSearch =
      !query ||
      [
        permit.permit_applicant,
        permit.permit_number,
        permit.aircraft_nationality,
        permit.aircraft_id_mark,
        permit.aircraft_owner,
        permit.aircraft_type,
        permit.aircraft_manufacturer,
        permit.serial_number,
        ...(permit.purpose_of_flight_display || []),
        permit.document_name
      ].some((value) => normalizeFlightPermitSearch(value).includes(query));
    return (
      matchesSearch &&
      (!validityStatus || permit.validity_status === validityStatus) &&
      (recommendation === null || permit.is_recommendation === recommendation) &&
      (!serialNumber || permit.serial_number === serialNumber)
    );
  });
}

export function calculateFlightPermitMetrics(permits) {
  const items = permits || [];
  return {
    total: items.length,
    active: items.filter((permit) => permit.validity_status === "active").length,
    expiring: items.filter((permit) => permit.validity_status === "expiring").length,
    expired: items.filter((permit) => permit.validity_status === "expired").length,
    documented: items.filter((permit) => permit.document_url).length
  };
}
