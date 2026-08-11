export function normalizePersonGroups(data) {
  return Array.isArray(data)
    ? data.map((group) => ({
        ...group,
        people: Array.isArray(group.people) ? group.people : []
      }))
    : [];
}
