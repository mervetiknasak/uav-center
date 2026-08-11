<script setup>
defineProps({
  checking: Boolean,
  mode: { type: String, required: true },
  credentials: { type: Object, required: true },
  title: { type: String, required: true },
  buttonLabel: { type: String, required: true },
  passwordsMatch: Boolean,
  submitDisabled: Boolean,
  loading: Boolean,
  error: { type: String, default: "" },
  registerMessage: { type: String, default: "" }
});

const emit = defineEmits(["submit", "switch-mode"]);
</script>

<template>
  <main v-if="checking" class="auth-shell">
    <n-spin size="large" />
  </main>

  <main v-else class="auth-shell">
    <section class="auth-panel">
      <div class="auth-heading">
        <p>UAV Center</p>
        <h1>{{ title }}</h1>
      </div>

      <n-tabs :value="mode" type="segment" @update:value="emit('switch-mode', $event)">
        <n-tab-pane name="login" tab="Giriş" />
        <n-tab-pane name="register" tab="Üyelik" />
      </n-tabs>

      <n-form class="auth-form" @submit.prevent="emit('submit')">
        <n-form-item label="Kullanıcı adı">
          <n-input
            v-model:value="credentials.username"
            autocomplete="username"
            placeholder="kullanici_adi"
          />
        </n-form-item>
        <n-form-item v-if="mode === 'register'" label="E-posta">
          <n-input
            v-model:value="credentials.email"
            autocomplete="email"
            placeholder="operator@example.com"
          />
        </n-form-item>
        <n-form-item label="Şifre">
          <n-input
            v-model:value="credentials.password"
            type="password"
            show-password-on="click"
            :autocomplete="mode === 'login' ? 'current-password' : 'new-password'"
            placeholder="••••••••"
          />
        </n-form-item>
        <n-form-item v-if="mode === 'register'" label="Şifre Tekrarı">
          <n-input
            v-model:value="credentials.passwordConfirm"
            type="password"
            show-password-on="click"
            autocomplete="new-password"
            placeholder="••••••••"
          />
        </n-form-item>
        <n-alert
          v-if="mode === 'register' && credentials.passwordConfirm && !passwordsMatch"
          type="warning"
          title="Şifre kontrolü"
        >
          Şifreler aynı olmalı.
        </n-alert>
        <n-alert v-if="error" type="error" title="Oturum hatası">{{ error }}</n-alert>
        <n-alert v-if="registerMessage" type="success" title="Üyelik isteği alındı">
          {{ registerMessage }}
        </n-alert>
        <n-button
          attr-type="submit"
          type="primary"
          block
          :loading="loading"
          :disabled="submitDisabled"
        >
          {{ buttonLabel }}
        </n-button>
      </n-form>
    </section>
  </main>
</template>
