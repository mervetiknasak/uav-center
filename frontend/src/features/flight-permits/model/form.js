export function createFlightPermitForm() {
  return {
    aircraft_number: "",
    permit_number: "",
    permit_type: "domestic",
    issuing_authority: "",
    flight_region: "",
    valid_from: null,
    valid_until: null,
    status: "approved",
    notes: ""
  };
}

export function flightPermitToForm(permit) {
  if (!permit) return createFlightPermitForm();
  return {
    aircraft_number: permit.aircraft_number,
    permit_number: permit.permit_number,
    permit_type: permit.permit_type,
    issuing_authority: permit.issuing_authority,
    flight_region: permit.flight_region,
    valid_from: permit.valid_from,
    valid_until: permit.valid_until,
    status: permit.status,
    notes: permit.notes
  };
}

export function buildFlightPermitPayload(form) {
  return {
    ...form,
    aircraft_number: String(form.aircraft_number || "")
      .trim()
      .toUpperCase(),
    permit_number: String(form.permit_number || "")
      .trim()
      .toUpperCase(),
    issuing_authority: String(form.issuing_authority || "").trim()
  };
}

export function selectExistingFlightPermitDocument(permit) {
  if (!permit?.document_url) return null;
  return {
    name: permit.document_name,
    url: permit.document_url,
    size: permit.document_size
  };
}
