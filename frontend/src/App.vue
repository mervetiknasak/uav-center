<script setup>
import { computed, onMounted, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { useAppContext } from "./app/bootstrap";
import { DEFAULT_ROUTE_NAME, menuSections } from "./app/navigation/menu";
import PwaInstallPrompt from "./app/components/PwaInstallPrompt.vue";
import AppSidebar from "./components/AppSidebar.vue";
import AuthPanel from "./components/AuthPanel.vue";

const { auth } = useAppContext();
const route = useRoute();
const router = useRouter();

const activeMenuKey = computed(() => route.meta.menuKey || DEFAULT_ROUTE_NAME);
const menuOptions = computed(() =>
  menuSections.filter((section) => !section.requiresAdmin || auth.currentUser.value?.is_staff)
);
const canRenderRoute = computed(
  () => !route.meta.requiresAdmin || Boolean(auth.currentUser.value?.is_staff)
);

function handleMenuUpdate(key) {
  router.push({ name: key });
}

watch(
  () => [route.name, route.meta.requiresAdmin, auth.currentUser.value],
  async ([, requiresAdmin, user]) => {
    if (user && requiresAdmin && !user.is_staff) {
      await router.replace({ name: DEFAULT_ROUTE_NAME });
    }
  }
);

onMounted(auth.loadSession);
</script>

<template>
  <n-config-provider>
    <n-message-provider>
      <n-dialog-provider>
        <AuthPanel
          v-if="auth.checking.value || !auth.currentUser.value"
          :checking="auth.checking.value"
          :mode="auth.mode.value"
          :credentials="auth.credentials.value"
          :title="auth.title.value"
          :button-label="auth.buttonLabel.value"
          :passwords-match="auth.passwordsMatch.value"
          :submit-disabled="auth.submitDisabled.value"
          :loading="auth.loading.value"
          :error="auth.error.value"
          :register-message="auth.registerMessage.value"
          @submit="auth.submit"
          @switch-mode="auth.switchMode"
        />

        <main v-else class="app-shell">
          <AppSidebar
            :user="auth.currentUser.value"
            :menu-key="activeMenuKey"
            :menu-options="menuOptions"
            :loading="auth.loading.value"
            @logout="auth.logout"
            @update:menu-key="handleMenuUpdate"
          />

          <section class="workspace">
            <router-view v-if="canRenderRoute" />
          </section>
        </main>

        <PwaInstallPrompt />
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>
