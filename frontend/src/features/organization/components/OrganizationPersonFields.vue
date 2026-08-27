<script setup>
import { computed } from "vue";

const props = defineProps({ person: { type: Object, required: true } });

const titles = computed(() => {
  if (Array.isArray(props.person.titles) && props.person.titles.length) return props.person.titles;
  return props.person.title ? [props.person.title] : [];
});
</script>

<template>
  <n-grid
    class="responsible-inline"
    :cols="12"
    :x-gap="12"
    :y-gap="6"
    responsive="screen"
    item-responsive
  >
    <n-grid-item span="12 m:2" class="responsible-cell">
      <n-tag v-if="person.username" size="small" :title="person.username">
        {{ person.username }}
      </n-tag>
      <span v-else>—</span>
    </n-grid-item>
    <n-grid-item span="12 m:3" class="responsible-cell responsible-name">
      <strong :title="person.name">{{ person.name }}</strong>
    </n-grid-item>
    <n-grid-item span="12 m:3" class="responsible-cell">
      <n-space v-if="titles.length" size="small">
        <n-tag v-for="title in titles" :key="title" size="small">{{ title }}</n-tag>
      </n-space>
      <span v-else>Görev bilgisi yok</span>
    </n-grid-item>
    <n-grid-item span="12 m:4" class="responsible-cell">
      <a v-if="person.email" :href="`mailto:${person.email}`" :title="person.email">
        {{ person.email }}
      </a>
      <span v-else>—</span>
    </n-grid-item>
  </n-grid>
</template>
