import { computed, ref } from "vue";
import { errorMessage } from "./errorMessage";

export function useAuth({ apiFetch, ensureCsrfToken, resetCsrfToken, onLogout }) {
  const checking = ref(true);
  const loading = ref(false);
  const mode = ref("login");
  const error = ref("");
  const registerMessage = ref("");
  const currentUser = ref(null);
  const credentials = ref({ username: "", email: "", password: "", passwordConfirm: "" });

  const title = computed(() => (mode.value === "login" ? "Giriş Yap" : "Yeni Üyelik"));
  const buttonLabel = computed(() => (mode.value === "login" ? "Giriş Yap" : "Üye Ol"));
  const passwordsMatch = computed(
    () =>
      credentials.value.password && credentials.value.password === credentials.value.passwordConfirm
  );
  const submitDisabled = computed(() => {
    if (!credentials.value.username || !credentials.value.password) return true;
    if (mode.value === "login") return false;
    return !credentials.value.email || !credentials.value.passwordConfirm || !passwordsMatch.value;
  });

  async function loadSession() {
    checking.value = true;
    error.value = "";
    try {
      await ensureCsrfToken();
      const data = await apiFetch("/api/auth/me/");
      currentUser.value = data.authenticated ? data.user : null;
    } catch (err) {
      error.value = errorMessage(err, "Oturum bilgisi alınamadı");
      currentUser.value = null;
    } finally {
      checking.value = false;
    }
  }

  async function submit() {
    loading.value = true;
    error.value = "";
    registerMessage.value = "";
    try {
      const payload =
        mode.value === "login"
          ? { username: credentials.value.username, password: credentials.value.password }
          : {
              username: credentials.value.username,
              email: credentials.value.email,
              password: credentials.value.password,
              password_confirm: credentials.value.passwordConfirm
            };
      const data = await apiFetch(`/api/auth/${mode.value}/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (mode.value === "register") {
        registerMessage.value = data.message || "Üyelik isteğiniz alındı. Admin onayı bekleniyor.";
        credentials.value = { username: "", email: "", password: "", passwordConfirm: "" };
        mode.value = "login";
        return;
      }

      currentUser.value = data.user;
      resetCsrfToken();
      credentials.value.password = "";
      credentials.value.passwordConfirm = "";
    } catch (err) {
      error.value = errorMessage(err, "İşlem tamamlanamadı");
    } finally {
      loading.value = false;
    }
  }

  async function logout() {
    loading.value = true;
    error.value = "";
    try {
      await apiFetch("/api/auth/logout/", { method: "POST" });
      currentUser.value = null;
      onLogout?.();
    } catch (err) {
      error.value = errorMessage(err, "Çıkış yapılamadı");
    } finally {
      loading.value = false;
    }
  }

  function switchMode(nextMode) {
    mode.value = nextMode;
    error.value = "";
    registerMessage.value = "";
  }

  return {
    checking,
    loading,
    mode,
    error,
    registerMessage,
    currentUser,
    credentials,
    title,
    buttonLabel,
    passwordsMatch,
    submitDisabled,
    loadSession,
    submit,
    logout,
    switchMode
  };
}
