export function groupTemplateFields(fields = []) {
  const groups = [];
  for (const field of fields) {
    let group = groups.find((item) => item.name === field.group);
    if (!group) {
      group = { name: field.group, fields: [] };
      groups.push(group);
    }
    group.fields.push(field);
  }
  return groups;
}

export function filterFormProcessRecords(records = [], filters = {}) {
  const search = String(filters.search || "")
    .trim()
    .toLocaleLowerCase("tr-TR");
  return records.filter((record) => {
    if (filters.process && record.process_code !== filters.process) return false;
    if (filters.template && record.template_code !== filters.template) return false;
    if (filters.status && record.status !== filters.status) return false;
    if (!search) return true;
    return [record.record_number, record.title, record.form_number, record.process_name].some(
      (value) =>
        String(value || "")
          .toLocaleLowerCase("tr-TR")
          .includes(search)
    );
  });
}
