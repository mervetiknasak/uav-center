import { ref } from "vue";
import { errorMessage } from "./errorMessage";

function normalizeGroups(data) {
  return Array.isArray(data)
    ? data.map((group) => ({ ...group, people: Array.isArray(group.people) ? group.people : [] }))
    : [];
}

export function useOrganization(apiFetch) {
  const projects = ref([]);
  const personGroups = ref([]);
  const loading = ref(false);
  const saving = ref(false);
  const error = ref("");

  async function loadOrganization() {
    loading.value = true;
    error.value = "";
    const results = await Promise.allSettled([
      apiFetch("/api/organization/projects/"),
      apiFetch("/api/organization/person-groups/")
    ]);
    const [projectResult, groupResult] = results;

    if (projectResult.status === "fulfilled") {
      projects.value = Array.isArray(projectResult.value) ? projectResult.value : [];
    }
    if (groupResult.status === "fulfilled") personGroups.value = normalizeGroups(groupResult.value);

    const errors = results
      .filter((result) => result.status === "rejected")
      .map((result) => errorMessage(result.reason, "Organizasyon bilgileri alınamadı"));
    if (errors.length) error.value = errors.join(" ");
    loading.value = false;
  }

  async function refreshPersonGroups() {
    personGroups.value = normalizeGroups(await apiFetch("/api/organization/person-groups/"));
  }

  async function refreshProjects() {
    const data = await apiFetch("/api/organization/projects/");
    projects.value = Array.isArray(data) ? data : [];
  }

  async function refreshType(type) {
    await (type === "group" || type === "person" ? refreshPersonGroups() : refreshProjects());
  }

  async function saveItem({ type, id, parentId, payload, done }) {
    saving.value = true;
    error.value = "";
    const paths = {
      project: id ? `/api/organization/projects/${id}/` : "/api/organization/projects/",
      panel: id ? `/api/organization/panels/${id}/` : `/api/organization/projects/${parentId}/panels/`,
      responsible: id
        ? `/api/organization/responsibles/${id}/`
        : `/api/organization/panels/${parentId}/responsibles/`,
      group: id ? `/api/organization/person-groups/${id}/` : "/api/organization/person-groups/",
      person: id ? `/api/organization/people/${id}/` : `/api/organization/person-groups/${parentId}/people/`
    };
    try {
      await apiFetch(paths[type], {
        method: id ? "PATCH" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      await refreshType(type);
      done?.();
    } catch (err) {
      error.value = errorMessage(err, "Kayıt kaydedilemedi");
    } finally {
      saving.value = false;
    }
  }

  async function deleteItem({ type, item }) {
    saving.value = true;
    error.value = "";
    const paths = {
      project: `/api/organization/projects/${item.id}/`,
      panel: `/api/organization/panels/${item.id}/`,
      responsible: `/api/organization/responsibles/${item.id}/`,
      group: `/api/organization/person-groups/${item.id}/`,
      person: `/api/organization/people/${item.id}/`
    };
    try {
      await apiFetch(paths[type], { method: "DELETE" });
      await refreshType(type);
    } catch (err) {
      error.value = errorMessage(err, "Kayıt silinemedi");
    } finally {
      saving.value = false;
    }
  }

  async function reorderResponsibles({ items }) {
    saving.value = true;
    error.value = "";
    try {
      await Promise.all(items.map((item) => apiFetch(`/api/organization/responsibles/${item.id}/`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ order: item.order })
      })));
      await loadOrganization();
    } catch (err) {
      error.value = errorMessage(err, "Sorumlu sıralaması güncellenemedi");
      await loadOrganization();
    } finally {
      saving.value = false;
    }
  }

  function resetOrganization() {
    projects.value = [];
    personGroups.value = [];
    error.value = "";
  }

  return {
    projects, personGroups, loading, saving, error,
    loadOrganization, saveItem, deleteItem, reorderResponsibles, resetOrganization
  };
}
