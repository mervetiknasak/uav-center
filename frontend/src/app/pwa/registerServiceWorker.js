export function registerServiceWorker({
  windowObject = globalThis.window,
  navigatorObject = globalThis.navigator,
  serviceWorkerUrl = `${import.meta.env.BASE_URL}sw.js`,
  scope = import.meta.env.BASE_URL
} = {}) {
  if (!import.meta.env.PROD || !navigatorObject?.serviceWorker) return;

  windowObject.addEventListener(
    "load",
    () => {
      navigatorObject.serviceWorker.register(serviceWorkerUrl, { scope }).catch((error) => {
        console.error("PWA service worker kaydı başarısız.", error);
      });
    },
    { once: true }
  );
}
