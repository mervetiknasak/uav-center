<script setup>
import {
  BadgeCheck,
  ChevronRight,
  KeyRound,
  Layers3,
  RefreshCw,
  Search,
  ShieldCheck,
  UserRoundCheck,
  UsersRound
} from "@lucide/vue";
import { computed, ref, watch } from "vue";

import {
  DEFAULT_ROLE_CATALOG,
  MEMBERSHIP_STATUS_OPTIONS,
  assignedRoleIds,
  filterMembershipUsers,
  filterRoleCatalog,
  groupRoleCatalog,
  membershipRoleOptions,
  rolesForUser,
  sameRoleSelection,
  updateRoleSelection,
  userInitials
} from "../model/membership";

const props = defineProps({
  users: {
    type: Array,
    required: true
  },
  roleCatalog: {
    type: Array,
    default: () => DEFAULT_ROLE_CATALOG
  },
  loading: {
    type: Boolean,
    required: true
  },
  error: {
    type: String,
    default: ""
  },
  updatingUserId: {
    type: Number,
    default: null
  }
});

const emit = defineEmits(["refresh", "update-status", "update-roles"]);

const searchQuery = ref("");
const statusFilter = ref("all");
const roleFilter = ref("all");
const editingUser = ref(null);
const roleQuery = ref("");
const draftRoleIds = ref([]);
const saveRequested = ref(false);

const roleFilterOptions = computed(() => membershipRoleOptions(props.roleCatalog));
const filteredUsers = computed(() =>
  filterMembershipUsers(
    props.users,
    {
      query: searchQuery.value,
      status: statusFilter.value,
      role: roleFilter.value
    },
    props.roleCatalog
  )
);
const activeUserCount = computed(() => props.users.filter((user) => user.is_active).length);
const assignedUserCount = computed(
  () => props.users.filter((user) => assignedRoleIds(user).length > 0).length
);
const hasActiveFilters = computed(
  () => searchQuery.value.trim() || statusFilter.value !== "all" || roleFilter.value !== "all"
);
const visibleRoleGroups = computed(() =>
  groupRoleCatalog(filterRoleCatalog(props.roleCatalog, roleQuery.value))
);
const hasRoleChanges = computed(
  () =>
    editingUser.value && !sameRoleSelection(draftRoleIds.value, assignedRoleIds(editingUser.value))
);
const isRoleEditorSaving = computed(
  () => editingUser.value && props.updatingUserId === editingUser.value.id
);

function userRoles(user) {
  return rolesForUser(user, props.roleCatalog);
}

function previewRoles(user) {
  return userRoles(user).slice(0, 3);
}

function additionalRoleCount(user) {
  return Math.max(userRoles(user).length - 3, 0);
}

function openRoleEditor(user) {
  if (!user.is_active) return;
  editingUser.value = user;
  draftRoleIds.value = [...assignedRoleIds(user)];
  roleQuery.value = "";
  saveRequested.value = false;
}

function closeRoleEditor(force = false) {
  if (isRoleEditorSaving.value && !force) return;
  editingUser.value = null;
  draftRoleIds.value = [];
  roleQuery.value = "";
  saveRequested.value = false;
}

function toggleDraftRole(roleId, enabled) {
  draftRoleIds.value = updateRoleSelection(draftRoleIds.value, roleId, enabled, props.roleCatalog);
}

function saveRoles() {
  if (!editingUser.value || !hasRoleChanges.value) return;
  saveRequested.value = true;
  emit("update-roles", editingUser.value, draftRoleIds.value);
}

function clearFilters() {
  searchQuery.value = "";
  statusFilter.value = "all";
  roleFilter.value = "all";
}

watch(
  () => props.updatingUserId,
  (currentUserId, previousUserId) => {
    if (!editingUser.value || !saveRequested.value) return;
    if (previousUserId === editingUser.value.id && currentUserId !== editingUser.value.id) {
      saveRequested.value = false;
      if (!props.error) closeRoleEditor(true);
    }
  }
);
</script>

<template>
  <section class="admin-membership-view">
    <div class="page-heading membership-page-heading">
      <div>
        <p>Admin</p>
        <h1>Üye Yönetimi</h1>
        <span>Kullanıcı erişimini, rollerini ve sorumluluklarını tek yerden yönetin.</span>
      </div>
      <n-button secondary :loading="loading" @click="emit('refresh')">
        <template #icon><RefreshCw :size="17" /></template>
        Listeyi Yenile
      </n-button>
    </div>

    <div class="membership-metrics" aria-label="Üyelik özeti">
      <div class="membership-metric">
        <span class="membership-metric-icon"><UsersRound :size="20" /></span>
        <div>
          <strong>{{ users.length }}</strong
          ><span>Toplam kullanıcı</span>
        </div>
      </div>
      <div class="membership-metric membership-metric-active">
        <span class="membership-metric-icon"><UserRoundCheck :size="20" /></span>
        <div>
          <strong>{{ activeUserCount }}</strong
          ><span>Aktif kullanıcı</span>
        </div>
      </div>
      <div class="membership-metric membership-metric-assigned">
        <span class="membership-metric-icon"><ShieldCheck :size="20" /></span>
        <div>
          <strong>{{ assignedUserCount }}</strong
          ><span>Rol atanmış kullanıcı</span>
        </div>
      </div>
    </div>

    <n-card size="small" class="membership-card">
      <div class="membership-role-guide">
        <div class="membership-role-guide-icon"><BadgeCheck :size="24" /></div>
        <div>
          <strong>Roller kategori bazında ve birlikte yönetilebilir</strong>
          <p>
            Bir kullanıcıya farklı çalışma alanlarından birden fazla rol atanabilir. Arama destekli
            rol seçiciyi açmak için kullanıcı satırındaki “Rolleri düzenle” seçeneğini kullanın.
          </p>
        </div>
      </div>

      <div class="membership-toolbar">
        <n-input v-model:value="searchQuery" clearable placeholder="Kullanıcı veya e-posta ara">
          <template #prefix><Search :size="17" /></template>
        </n-input>
        <n-select
          v-model:value="statusFilter"
          :options="MEMBERSHIP_STATUS_OPTIONS"
          aria-label="Kullanıcı durumuna göre filtrele"
        />
        <n-select
          v-model:value="roleFilter"
          filterable
          :options="roleFilterOptions"
          aria-label="Role göre filtrele"
        />
      </div>

      <n-alert v-if="error" type="error" title="Üye yönetimi hatası">
        {{ error }}
      </n-alert>

      <div class="membership-list-heading">
        <div>
          <strong>Kullanıcılar</strong>
          <span>{{ filteredUsers.length }} kullanıcı gösteriliyor</span>
        </div>
        <n-button v-if="hasActiveFilters" text type="primary" @click="clearFilters">
          Filtreleri temizle
        </n-button>
      </div>

      <n-spin :show="loading">
        <n-empty
          v-if="filteredUsers.length === 0"
          :description="
            hasActiveFilters ? 'Filtrelere uygun kullanıcı bulunamadı' : 'Henüz kullanıcı yok'
          "
        />
        <div v-else class="membership-user-list">
          <article v-for="user in filteredUsers" :key="user.id" class="membership-user-card">
            <div class="membership-user-identity">
              <div class="membership-avatar" aria-hidden="true">
                {{ userInitials(user.username) }}
              </div>
              <div class="membership-user-copy">
                <div class="membership-user-name">
                  <strong>{{ user.username }}</strong>
                  <n-tag :type="user.is_active ? 'success' : 'default'" size="small" round>
                    {{ user.is_active ? "Aktif" : "Pasif" }}
                  </n-tag>
                  <n-tag v-if="user.is_staff" type="info" size="small" round>Admin</n-tag>
                </div>
                <span>{{ user.email || "E-posta bilgisi yok" }}</span>
              </div>
            </div>

            <div class="membership-permissions">
              <div class="membership-permissions-heading">
                <div>
                  <strong>Roller ve yetkiler</strong>
                  <span v-if="user.is_active"> {{ userRoles(user).length }} rol atanmış </span>
                  <span v-else>Rol düzenlemek için kullanıcıyı etkinleştirin</span>
                </div>
                <span v-if="updatingUserId === user.id" class="membership-saving">
                  Kaydediliyor…
                </span>
              </div>

              <div v-if="userRoles(user).length" class="membership-role-summary">
                <n-tag
                  v-for="role in previewRoles(user)"
                  :key="role.id"
                  size="small"
                  :bordered="false"
                >
                  {{ role.name }}
                </n-tag>
                <n-tag v-if="additionalRoleCount(user)" size="small" round>
                  +{{ additionalRoleCount(user) }} rol
                </n-tag>
              </div>
              <div v-else class="membership-role-empty">
                <KeyRound :size="16" />
                <span>Henüz rol atanmamış</span>
              </div>

              <n-button
                size="small"
                secondary
                class="membership-edit-roles-button"
                :disabled="!user.is_active || updatingUserId === user.id"
                @click="openRoleEditor(user)"
              >
                Rolleri düzenle
                <ChevronRight :size="15" />
              </n-button>
            </div>

            <div class="membership-account-action">
              <span>Hesap erişimi</span>
              <n-button
                v-if="!user.is_active"
                size="small"
                type="primary"
                secondary
                :loading="updatingUserId === user.id"
                @click="emit('update-status', user, true)"
              >
                Etkinleştir
              </n-button>
              <n-button
                v-else
                size="small"
                type="error"
                secondary
                :loading="updatingUserId === user.id"
                @click="emit('update-status', user, false)"
              >
                Devre Dışı Bırak
              </n-button>
            </div>
          </article>
        </div>
      </n-spin>
    </n-card>

    <n-drawer
      :show="Boolean(editingUser)"
      width="min(580px, 100vw)"
      placement="right"
      @update:show="!$event && closeRoleEditor()"
    >
      <n-drawer-content title="Roller ve Yetkiler" closable>
        <div v-if="editingUser" class="membership-role-editor">
          <div class="membership-editor-user">
            <div class="membership-avatar" aria-hidden="true">
              {{ userInitials(editingUser.username) }}
            </div>
            <div>
              <strong>{{ editingUser.username }}</strong>
              <span>{{ editingUser.email || "E-posta bilgisi yok" }}</span>
            </div>
            <n-tag v-if="editingUser.is_staff" type="info" size="small" round>
              Sistem rolü: Admin
            </n-tag>
          </div>

          <n-alert v-if="error" type="error" title="Roller kaydedilemedi">
            {{ error }}
          </n-alert>

          <div class="membership-editor-intro">
            <Layers3 :size="20" />
            <p>
              Roller çalışma alanlarına göre gruplanır. Kullanıcının sorumlulukları için gereken tüm
              rolleri seçebilirsiniz.
            </p>
          </div>

          <n-input v-model:value="roleQuery" clearable placeholder="Rol, yetki veya kategori ara">
            <template #prefix><Search :size="17" /></template>
          </n-input>

          <n-empty
            v-if="visibleRoleGroups.length === 0"
            description="Aramanızla eşleşen rol bulunamadı"
          />
          <div v-else class="membership-role-groups">
            <section
              v-for="group in visibleRoleGroups"
              :key="group.id"
              class="membership-role-group"
            >
              <div class="membership-role-group-heading">
                <div>
                  <strong>{{ group.label }}</strong>
                  <span>{{ group.description }}</span>
                </div>
                <n-tag size="small" round>{{ group.roles.length }} rol</n-tag>
              </div>

              <div class="membership-role-picker-list">
                <n-checkbox
                  v-for="role in group.roles"
                  :key="role.id"
                  class="membership-role-picker-option"
                  :class="{
                    'membership-role-picker-option-selected': draftRoleIds.includes(role.id)
                  }"
                  :checked="draftRoleIds.includes(role.id)"
                  :disabled="isRoleEditorSaving"
                  @update:checked="toggleDraftRole(role.id, $event)"
                >
                  <span class="membership-role-picker-copy">
                    <strong>{{ role.name }}</strong>
                    <span>{{ role.title }}</span>
                    <small>{{ role.description }}</small>
                  </span>
                </n-checkbox>
              </div>
            </section>
          </div>
        </div>

        <template #footer>
          <div class="membership-editor-footer">
            <div>
              <strong>{{ draftRoleIds.length }} rol seçildi</strong>
              <span v-if="hasRoleChanges">Kaydedilmemiş değişiklikler var</span>
              <span v-else>Rol seçimi güncel</span>
            </div>
            <n-space>
              <n-button :disabled="isRoleEditorSaving" @click="closeRoleEditor">Vazgeç</n-button>
              <n-button
                type="primary"
                :disabled="!hasRoleChanges"
                :loading="isRoleEditorSaving"
                @click="saveRoles"
              >
                Değişiklikleri Kaydet
              </n-button>
            </n-space>
          </div>
        </template>
      </n-drawer-content>
    </n-drawer>
  </section>
</template>
