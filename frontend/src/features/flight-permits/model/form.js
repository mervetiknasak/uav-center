export function createFlightPermitForm(templateCode = "institution_a") {
  return {
    permit_applicant: "",
    permit_number: "",
    template_code: templateCode,
    template_data: {},
    aircraft_nationality: "",
    aircraft_id_mark: "",
    aircraft_owner: "",
    aircraft_type: "",
    aircraft_manufacturer: "",
    serial_number: "",
    purpose_of_flight: [],
    target_date: null,
    flight_duration: null,
    aircraft_configuration: "",
    conditions_restrictions: "",
    conditions_substantiations: "",
    is_recommendation: false,
    valid_from: null,
    valid_until: null,
    status: "approved",
    notes: ""
  };
}

export function flightPermitToForm(permit) {
  if (!permit) return createFlightPermitForm();
  return {
    permit_applicant: permit.permit_applicant,
    permit_number: permit.permit_number,
    template_code: permit.template_code || "institution_a",
    template_data: { ...(permit.template_data || {}) },
    aircraft_nationality: permit.aircraft_nationality,
    aircraft_id_mark: permit.aircraft_id_mark,
    aircraft_owner: permit.aircraft_owner,
    aircraft_type: permit.aircraft_type,
    aircraft_manufacturer: permit.aircraft_manufacturer,
    serial_number: permit.serial_number,
    purpose_of_flight: [...(permit.purpose_of_flight || [])],
    target_date: permit.target_date,
    flight_duration: permit.flight_duration,
    aircraft_configuration: permit.aircraft_configuration,
    conditions_restrictions: permit.conditions_restrictions,
    conditions_substantiations: permit.conditions_substantiations,
    is_recommendation: permit.is_recommendation,
    valid_from: permit.valid_from,
    valid_until: permit.valid_until,
    status: permit.status,
    notes: permit.notes
  };
}

export function buildFlightPermitPayload(form) {
  return {
    ...form,
    permit_applicant: String(form.permit_applicant || "").trim(),
    aircraft_nationality: String(form.aircraft_nationality || "")
      .trim()
      .toUpperCase(),
    aircraft_id_mark: String(form.aircraft_id_mark || "")
      .trim()
      .toUpperCase(),
    permit_number: String(form.permit_number || "")
      .trim()
      .toUpperCase(),
    template_code: form.template_code,
    template_data: { ...(form.template_data || {}) },
    aircraft_owner: String(form.aircraft_owner || "").trim(),
    aircraft_type: String(form.aircraft_type || "").trim(),
    aircraft_manufacturer: String(form.aircraft_manufacturer || "").trim(),
    serial_number: String(form.serial_number || "")
      .trim()
      .toUpperCase(),
    purpose_of_flight: [...(form.purpose_of_flight || [])],
    target_date: form.target_date || "",
    flight_duration: form.flight_duration ?? ""
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
