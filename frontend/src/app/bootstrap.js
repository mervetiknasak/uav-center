import { inject } from "vue";

import { useApi } from "../composables/useApi";
import { useAuth } from "../composables/useAuth";

const APP_CONTEXT_KEY = Symbol("uav-center-app-context");

export function createAppContext() {
  const api = useApi();
  const auth = useAuth({
    apiFetch: api.apiFetch,
    ensureCsrfToken: api.ensureCsrfToken,
    resetCsrfToken: api.resetCsrfToken
  });

  return Object.freeze({ api, auth });
}

export function installAppContext(app, context) {
  app.provide(APP_CONTEXT_KEY, context);
}

export function useAppContext() {
  const context = inject(APP_CONTEXT_KEY, null);
  if (!context) {
    throw new Error("Uygulama context'i kurulmadan feature controller kullanılamaz.");
  }
  return context;
}
