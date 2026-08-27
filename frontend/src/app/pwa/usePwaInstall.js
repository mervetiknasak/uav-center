import { computed, ref, shallowRef } from "vue";

function matchesStandalone(windowObject, navigatorObject) {
  return Boolean(
    navigatorObject?.standalone || windowObject?.matchMedia?.("(display-mode: standalone)").matches
  );
}

function isIosDevice(navigatorObject) {
  return /iphone|ipad|ipod/i.test(navigatorObject?.userAgent || "");
}

export function usePwaInstall({
  windowObject = globalThis.window,
  navigatorObject = globalThis.navigator
} = {}) {
  const deferredPrompt = shallowRef(null);
  const installed = ref(matchesStandalone(windowObject, navigatorObject));
  const dismissed = ref(false);
  const isInstalling = ref(false);
  const error = ref("");
  const isManualInstall = computed(
    () => isIosDevice(navigatorObject) && !deferredPrompt.value && !installed.value
  );
  const shouldShow = computed(
    () =>
      !installed.value &&
      !dismissed.value &&
      Boolean(deferredPrompt.value || isManualInstall.value || error.value)
  );

  function handleInstallPrompt(event) {
    if (installed.value) return;
    event.preventDefault();
    deferredPrompt.value = event;
    dismissed.value = false;
    error.value = "";
  }

  function handleInstalled() {
    installed.value = true;
    deferredPrompt.value = null;
    error.value = "";
  }

  function start() {
    windowObject?.addEventListener?.("beforeinstallprompt", handleInstallPrompt);
    windowObject?.addEventListener?.("appinstalled", handleInstalled);
  }

  function stop() {
    windowObject?.removeEventListener?.("beforeinstallprompt", handleInstallPrompt);
    windowObject?.removeEventListener?.("appinstalled", handleInstalled);
  }

  function dismiss() {
    dismissed.value = true;
    error.value = "";
  }

  async function requestInstall() {
    const prompt = deferredPrompt.value;
    if (!prompt || isInstalling.value) return null;

    isInstalling.value = true;
    error.value = "";
    try {
      const result = await prompt.prompt();
      deferredPrompt.value = null;
      dismissed.value = true;
      return result;
    } catch {
      deferredPrompt.value = null;
      error.value =
        "Kurulum penceresi açılamadı. Tarayıcı menüsündeki yükleme seçeneğini kullanın.";
      return null;
    } finally {
      isInstalling.value = false;
    }
  }

  return {
    shouldShow,
    isManualInstall,
    isInstalling,
    error,
    start,
    stop,
    dismiss,
    requestInstall
  };
}
