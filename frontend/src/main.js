import { createApp } from "vue";

import App from "./App.vue";
import { createAppContext, installAppContext } from "./app/bootstrap";
import { registerServiceWorker } from "./app/pwa/registerServiceWorker";
import { ui } from "./app/ui";
import router from "./router";
import "./style.css";

const app = createApp(App);
const appContext = createAppContext();

installAppContext(app, appContext);
app.use(ui).use(router).mount("#app");
registerServiceWorker();
