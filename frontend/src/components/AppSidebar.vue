<script setup>
defineProps({
  user: { type: Object, required: true },
  menuKey: { type: String, required: true },
  menuOptions: { type: Array, required: true },
  loading: Boolean
});

const emit = defineEmits(["logout", "update:menu-key"]);
</script>

<template>
  <aside class="toolbox-sidebar">
    <div class="toolbox-brand">
      <span>UAV Center</span>
      <strong>Toolbox</strong>
    </div>
    <div class="session-box">
      <span>Oturum</span>
      <strong>{{ user.username }}</strong>
      <small v-if="user.is_staff">Admin</small>
      <n-button size="small" secondary :loading="loading" @click="emit('logout')"
        >Çıkış Yap</n-button
      >
    </div>
    <n-menu
      class="toolbox-menu"
      :value="menuKey"
      :options="menuOptions"
      :indent="18"
      :default-expanded-keys="
        user.is_staff
          ? ['document-management', 'organization', 'tools', 'operations', 'system', 'admin']
          : ['document-management', 'organization', 'tools', 'operations']
      "
      @update:value="emit('update:menu-key', $event)"
    />
  </aside>
</template>
