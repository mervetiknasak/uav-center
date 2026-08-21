export const EDK_STATUS_OPTIONS = [
  { label: "Onay Bekliyor", value: "pending" },
  { label: "Onaylandı", value: "approved" },
  { label: "Reddedildi", value: "rejected" }
];

export const EDK_STATUS_TAG_TYPES = {
  pending: "warning",
  approved: "success",
  rejected: "error"
};

export function filterEdkApplications(applications, filters) {
  const search = String(filters.search || "")
    .trim()
    .toLocaleLowerCase("tr-TR");

  return applications.filter((application) => {
    if (filters.status && application.status !== filters.status) return false;
    if (filters.applicant && application.applicant_name !== filters.applicant) return false;
    if (!search) return true;

    return [
      `EDK-${application.id}`,
      application.meeting_title,
      application.project_name,
      application.applicant_name,
      application.location
    ].some((value) =>
      String(value || "")
        .toLocaleLowerCase("tr-TR")
        .includes(search)
    );
  });
}

export function formatEdkDateTime(value) {
  if (!value) return "—";
  return new Intl.DateTimeFormat("tr-TR", {
    dateStyle: "short",
    timeStyle: "short"
  }).format(new Date(value));
}
