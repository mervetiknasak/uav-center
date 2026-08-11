export function normalizeFlightPermitSearch(value) {
  return String(value || "")
    .toLocaleLowerCase("tr-TR")
    .trim();
}

export function selectAircraftOptions(permits) {
  return [...new Set((permits || []).map((permit) => permit.aircraft_number))]
    .sort((a, b) => a.localeCompare(b, "tr"))
    .map((value) => ({ label: value, value }));
}

export function filterFlightPermits(
  permits,
  { search = "", validityStatus = null, permitType = null, aircraft = null } = {}
) {
  const query = normalizeFlightPermitSearch(search);
  return (permits || []).filter((permit) => {
    const matchesSearch =
      !query ||
      [
        permit.aircraft_number,
        permit.permit_number,
        permit.issuing_authority,
        permit.flight_region,
        permit.document_name
      ].some((value) => normalizeFlightPermitSearch(value).includes(query));
    return (
      matchesSearch &&
      (!validityStatus || permit.validity_status === validityStatus) &&
      (!permitType || permit.permit_type === permitType) &&
      (!aircraft || permit.aircraft_number === aircraft)
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
