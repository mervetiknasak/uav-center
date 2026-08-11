import { ref } from "vue";

import { errorMessage } from "./errorMessage";

export function useOrganizationProjects(apiFetch) {
  const projects = ref([]);
  const loading = ref(false);
  const error = ref("");

  async function loadProjects() {
    loading.value = true;
    error.value = "";
    try {
      const data = await apiFetch("/api/organization/projects/");
      projects.value = Array.isArray(data) ? data : [];
    } catch (err) {
      error.value = errorMessage(err, "Proje bilgileri alınamadı");
    } finally {
      loading.value = false;
    }
  }

  function resetProjects() {
    projects.value = [];
    error.value = "";
  }

  return { projects, loading, error, loadProjects, resetProjects };
}
